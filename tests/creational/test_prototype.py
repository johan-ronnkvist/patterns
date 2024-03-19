from patterns.creational.prototype import Prototype
from patterns.structural.composite import Composite


class Spice(Prototype["Spice"]):
    def __init__(self, name: str):
        self.name = name


type SpiceMix = Composite[Spice]


class TestPrototype:
    def test_clone_complex_object(self):
        pass
