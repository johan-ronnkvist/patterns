from abc import ABCMeta, abstractmethod
from collections.abc import Iterator


class Repository[K, T](metaclass=ABCMeta):
    @abstractmethod
    def get(self, key: K, default: T | None = None) -> T:
        raise NotImplementedError

    @abstractmethod
    def __getitem__(self, key: K) -> T:
        raise NotImplementedError

    @abstractmethod
    def save(self, value: T) -> None:
        raise NotImplementedError

    @abstractmethod
    def __delitem__(self, key: K) -> None:
        raise NotImplementedError

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def __contains__(self, key: K) -> bool:
        raise NotImplementedError

    @abstractmethod
    def __iter__(self) -> Iterator[K]:
        raise NotImplementedError

    @abstractmethod
    def items(self) -> Iterator[tuple[K, T]]:
        raise NotImplementedError

    @abstractmethod
    def keys(self) -> Iterator[K]:
        raise NotImplementedError

    @abstractmethod
    def values(self) -> Iterator[T]:
        raise NotImplementedError


class Transaction[T, K](metaclass=ABCMeta):
    @abstractmethod
    def __enter__(self) -> Repository[T, K]:
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError


class Database[T, Y](metaclass=ABCMeta):
    @abstractmethod
    def transaction(self) -> Transaction[T, Y]:
        raise NotImplementedError
