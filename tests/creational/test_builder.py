import pytest

from patterns.creational.builder import Builder, DelayedCreation


class Brick:
    def __init__(self, color: str):
        self.color = color


class Spice:
    def __init__(self, name: str):
        self.name = name


class Salt(Spice):
    def __init__(self):
        super().__init__("salt")


class Pepper(Spice):
    def __init__(self):
        super().__init__("pepper")


class Chili(Spice):
    def __init__(self, variety: str = "jalapeno"):
        super().__init__(f" {variety} chili")


class Herb(Spice):
    def __init__(self, name: str):
        super().__init__(name)


class SaltySpiceMix(Spice):
    def __init__(self, salt: Salt, spice: Spice):
        super().__init__(f"{salt.name} and {spice.name}")


def spice_factory(name: str = "cinnamon") -> Spice:
    return Spice(name)


def spice_mix_factory(salt: Salt, spice: Spice) -> SaltySpiceMix:
    return SaltySpiceMix(salt, spice)


class TestBuilderRegistration:
    def test_register_type(self, builder: Builder):
        builder.register(Spice)

    def test_register_type_with_kwargs(self, builder: Builder):
        builder.register(Spice, name="cumin")

    def test_register_type_with_instance(self, builder: Builder):
        builder.register(Spice, instance=Spice(name="cumin"))

    def test_register_type_with_alias(self, builder: Builder):
        builder.register(Herb, alias=Spice)

    def test_register_type_with_kwargs_and_alias(self, builder: Builder):
        builder.register(Herb, name="cumin", alias=Spice)

    def test_register_type_with_kwargs_instance(self, builder: Builder):
        with pytest.raises(ValueError):
            builder.register(Herb, name="cumin", instance=Herb(name="parsley"))

    def test_register_type_with_instance_and_alias(self, builder: Builder):
        builder.register(Herb, instance=Herb(name="cumin"), alias=Spice)

    def test_register_existing_type(self, builder: Builder):
        builder.register(Spice)
        with pytest.raises(ValueError):
            builder.register(Spice)

    def test_register_type_that_collides_with_existing_alias(self, builder: Builder):
        builder.register(Herb, alias=Spice)
        with pytest.raises(ValueError):
            builder.register(Spice)

    def test_register_alias_that_collides_with_existing_type(self, builder: Builder):
        builder.register(Spice)
        with pytest.raises(ValueError):
            builder.register(Herb, alias=Spice)

    def test_register_alias_that_collides_with_existing_alias(self, builder: Builder):
        builder.register(Herb, alias=Spice)
        with pytest.raises(ValueError):
            builder.register(Salt, alias=Spice)

    def test_builder_contains_type_after_registration(self, builder: Builder):
        assert Spice not in builder
        builder.register(Spice)
        assert Spice in builder

    def test_builder_contains_alias_after_registration(self, builder: Builder):
        assert Spice not in builder
        builder.register(Herb, alias=Spice)
        assert Spice in builder

    def test_register_type_with_invalid_instance_type(self, builder: Builder):
        with pytest.raises(ValueError):
            builder.register(Spice, instance=str("test"))

    def test_register_type_with_invalid_alias_type(self, builder: Builder):
        with pytest.raises(ValueError):
            builder.register(Herb, alias=str)

    def test_register_type_with_factory(self, builder: Builder):
        builder.register(Spice, factory=spice_factory)

    def test_register_type_with_factory_and_alias(self, builder: Builder):
        builder.register(
            SaltySpiceMix,
            factory=spice_mix_factory,
            alias=Spice,
            salt=Salt(),
            spice=Spice(name="cumin"),
        )
        spice = builder.resolve(Spice)
        assert isinstance(spice, SaltySpiceMix)

    def test_register_type_with_invalid_factory(self, builder: Builder):
        with pytest.raises(ValueError):
            builder.register(Herb, factory=spice_factory)

    def test_register_type_with_factory_and_instance(self, builder: Builder):
        with pytest.raises(ValueError):
            builder.register(Spice, factory=spice_factory, instance=Spice(name="cumin"))

    def test_register_type_with_lazy_init_instance(self, builder: Builder):
        builder.register(Spice, instance=DelayedCreation, factory=spice_factory)
        spice = builder.resolve(Spice)
        assert isinstance(spice, Spice)


class TestBuilderResolution:
    def test_resolve_existing_type(self, builder: Builder):
        builder.register(Salt)
        salt = builder.resolve(Salt)
        assert isinstance(salt, Salt)

    def test_resolve_missing_type(self, builder: Builder):
        with pytest.raises(ValueError):
            builder.resolve(Salt)

    def test_resolve_type_with_kwargs(self, builder: Builder):
        builder.register(Spice, name="cumin")
        spice = builder.resolve(Spice)
        assert isinstance(spice, Spice)
        assert spice.name == "cumin"

    def test_resolve_type_with_instance(self, builder: Builder):
        spice = Spice(name="cumin")
        builder.register(Spice, instance=spice)
        resolved_spice = builder.resolve(Spice)
        assert resolved_spice is spice

    def test_resolve_type_with_alias(self, builder: Builder):
        builder.register(Herb, alias=Spice, name="cumin")
        spice = builder.resolve(Spice)
        assert isinstance(spice, Herb)

    def test_resolve_type_with_kwarg_override(self, builder: Builder):
        builder.register(Herb, name="oregano")
        spice = builder.resolve(Herb, name="parsley")
        assert isinstance(spice, Herb)
        assert spice.name == "parsley"

    def test_resolve_type_with_default_argument(self, builder: Builder):
        builder.register(Chili)
        chili = builder.resolve(Chili)
        assert isinstance(chili, Chili)
        assert chili.name == " jalapeno chili"

    def test_resolve_type_with_default_argument_override(self, builder: Builder):
        builder.register(Chili)
        chili = builder.resolve(Chili, variety="habanero")
        assert isinstance(chili, Chili)
        assert chili.name == " habanero chili"

    def test_resolve_type_with_dependency(self, builder: Builder):
        builder.register(Salt)
        builder.register(Pepper, alias=Spice)
        builder.register(SaltySpiceMix)
        # Builder will resolve Salt and Spice (alias for Pepper) and pass them to SaltySpiceMix
        mix = builder.resolve(SaltySpiceMix)
        assert isinstance(mix, SaltySpiceMix)
        assert mix.name == "salt and pepper"

    def test_resolve_type_with_missing_dependency(self, builder: Builder):
        builder.register(Salt)
        builder.register(SaltySpiceMix)
        with pytest.raises(ValueError):
            builder.resolve(SaltySpiceMix)

    def test_resolve_type_with_dependency_override(self, builder: Builder):
        builder.register(Salt)
        builder.register(SaltySpiceMix)
        mix = builder.resolve(SaltySpiceMix, spice=Spice(name="cumin"))
        assert isinstance(mix, SaltySpiceMix)
        assert mix.name == "salt and cumin"

    def test_resolve_type_from_factory(self, builder: Builder):
        builder.register(Spice, factory=spice_factory)
        spice = builder.resolve(Spice)
        assert isinstance(spice, Spice)
        assert spice.name == "cinnamon"

    def test_resolve_type_from_factory_with_kwarg_override(self, builder: Builder):
        builder.register(Spice, factory=spice_factory)
        spice = builder.resolve(Spice, name="cumin")
        assert isinstance(spice, Spice)
        assert spice.name == "cumin"

    def test_resolve_type_with_kwargs_from_factory(self, builder: Builder):
        builder.register(Spice, factory=spice_factory, name="cumin")
        spice = builder.resolve(Spice)
        assert isinstance(spice, Spice)
        assert spice.name == "cumin"

    def test_resolve_type_from_factory_with_dependency(self, builder: Builder):
        builder.register(Salt)
        builder.register(Spice, factory=spice_factory, name="nutmeg")
        builder.register(SaltySpiceMix, factory=spice_mix_factory)
        mix = builder.resolve(SaltySpiceMix)
        assert isinstance(mix, SaltySpiceMix)
        assert mix.name == "salt and nutmeg"

    def test_resolve_type_from_factory_with_provided_dependencies(
        self, builder: Builder
    ):
        builder.register(SaltySpiceMix, factory=spice_mix_factory)
        mix = builder.resolve(SaltySpiceMix, spice=Spice(name="cumin"), salt=Salt())
        assert isinstance(mix, SaltySpiceMix)
        assert mix.name == "salt and cumin"
