from collections.abc import Iterator
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import create_engine, types
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from patterns.structural import repository as base


@dataclass(frozen=True)
class Item:
    name: str
    uuid: UUID


class Base(DeclarativeBase):
    pass


class DbItem(Base):
    __tablename__ = "items"

    uuid: Mapped[UUID] = mapped_column(types.UUID, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(types.String, nullable=False)

    @classmethod
    def from_domain(cls, item: Item) -> "DbItem":
        return cls(uuid=item.uuid, name=item.name)

    def to_domain(self) -> Item:
        return Item(name=self.name, uuid=self.uuid)


type K = UUID
type T = Item


class Repository(base.Repository[K, T]):
    def __init__(self, session: Session):
        self._session = session

    def get(self, key: K, default: T | None = None) -> T:
        found = self._session.query(DbItem).get(key)
        return found.to_domain() if found else default

    def __getitem__(self, key: K) -> T:
        found = self.get(key)
        if not found:
            raise KeyError(key)
        return found

    def save(self, item: T) -> None:
        self._session.add(DbItem.from_domain(item))

    def __delitem__(self, key: K) -> None:
        self._session.delete(self[key])

    def __len__(self) -> int:
        return self._session.query(DbItem).count()

    def __contains__(self, key: K | T) -> bool:
        if isinstance(key, Item):
            key = key.uuid
        return bool(self.get(key))

    def __iter__(self) -> Iterator[K]:
        return iter(self.keys())

    def items(self) -> Iterator[tuple[K, T]]:
        pass

    def keys(self) -> Iterator[K]:
        return iter(item.uuid for item in self._session.query(DbItem))

    def values(self) -> Iterator[T]:
        return iter(item.to_domain() for item in self._session.query(DbItem))
        pass


class Transaction(base.Transaction[T, K]):
    def __init__(self, session: Session):
        self._session = session

    def __enter__(self) -> Repository:
        return Repository(self._session)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()


class Database(base.Database[T, K]):
    def __init__(self, uri: str):
        self._engine = create_engine(uri)
        self._factory = sessionmaker(self._engine)
        DbItem.metadata.create_all(self._engine)

    def transaction(self) -> Transaction:
        return Transaction(self._factory())
