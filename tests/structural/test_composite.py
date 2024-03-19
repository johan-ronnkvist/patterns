from structural.composite import Composite


class Spice:
    def __init__(self, name: str):
        self.name = name


class SpiceMix(Spice, Composite[Spice]):
    def __init__(self, name: str, spices: set[Spice] = None):
        super().__init__(name)
        self._spices: set[Spice] = set(spices) if spices else set()

    def append(self, item: Spice) -> None:
        self._spices.add(item)



class TestComposite:
    def test_spice_mix_with_single_spice(self):
        mix = SpiceMix([Spice("cumin"), Spice("cinnamon")])
        assert len(mix.items) == 2
