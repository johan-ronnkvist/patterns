import pytest

from patterns.creational.builder import Builder


@pytest.fixture
def builder() -> Builder:
    return Builder()
