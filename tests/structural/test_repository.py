from uuid import UUID, uuid4

from examples.structural import repository


def make_item(uuid: UUID | None = None, name: str = "item") -> repository.Item:
    return repository.Item(uuid=uuid or uuid4(), name=name)


class TestRepository:
    def test_insert_item(self, transaction):
        item = make_item()
        with transaction as repo:
            assert item.uuid not in repo
            repo.save(item)
            assert item.uuid in repo
