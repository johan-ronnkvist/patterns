import pytest

from examples.structural import repository


@pytest.fixture
def database() -> repository.Database:
    return repository.Database("sqlite:///:memory:")


@pytest.fixture
def transaction(database: repository.Database) -> repository.Transaction:
    return database.transaction()
