import inspect
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel, model_validator

_logger = logging.getLogger(__name__)


class RegistrationError(ValueError):
    pass


class ResolutionError(ValueError):
    pass


class DelayedCreation(BaseModel):
    pass


class Context(BaseModel):
    typename: type
    aliases: set[type] = set()
    kwargs: dict[str, Any] = {}
    instance: Any | DelayedCreation = None
    factory: Callable | None = None

    @model_validator(mode="after")
    def validate_model(self) -> "Context":
        self._validate_instance()
        self._validate_aliases()
        self._validate_factory()

        return self

    def _validate_instance(self):
        if isinstance(self.instance, DelayedCreation):
            self.instance = DelayedCreation

        if self.instance and self.instance is not DelayedCreation:
            if not isinstance(self.instance, self.typename):
                raise ValueError(f"Instance {self.instance} is not of type {self.typename}")

            if self.kwargs:
                raise ValueError("Cannot provide instance when using kwargs")

            if self.factory:
                raise ValueError("Cannot provide instance when using factory")

    def _validate_aliases(self):
        if self.aliases:
            for alias in self.aliases:
                if not issubclass(self.typename, alias):
                    raise ValueError(f"{self.typename} is not a subclass of {alias}")

    def _validate_factory(self):
        if self.factory:
            factory_signature = inspect.signature(self.factory)
            if factory_signature.return_annotation != self.typename:
                raise ValueError(
                    f"Return type {factory_signature.return_annotation} does not match {self.typename}"
                )

    def resolve(self, builder: "Builder", **kwargs) -> Any:
        return self._instance(builder, **kwargs) or self._create(builder, **kwargs)

    def _instance(self, builder: "Builder", **kwargs) -> Any:
        if self.instance is DelayedCreation:
            self.instance = self._create(builder, **kwargs)
        return self.instance

    def _create(self, builder: "Builder", **kwargs) -> Any:
        """Resolve the type from the context using the provided builder.

        Resolution of arguments is done in the following order:
        1. If a parameter is provided in kwargs, use it.
        2. Else, if a parameter exists in self._kwargs, use it.
        3. Else, if a parameter has a default value, use it.
        4. Else, resolve from builder

        Args:
            builder: The builder to use for resolving the type.
            kwargs: Additional keyword arguments to use for resolving the type.
        """

        # Inspect signature and remove 'self, *args and **kwargs' from it
        signature = inspect.signature(self.factory or self.typename.__init__)
        excluded_params = ["self", "args", "kwargs"]
        trimmed_params = [
            param for param in signature.parameters.values() if param.name not in excluded_params
        ]
        signature = signature.replace(parameters=trimmed_params)

        resolved_kwargs = self.kwargs.copy()

        for param in signature.parameters.values():
            if param.name in kwargs:
                resolved_kwargs[param.name] = kwargs[param.name]
            elif param.name in self.kwargs:
                resolved_kwargs[param.name] = self.kwargs[param.name]
            elif param.default != param.empty:
                resolved_kwargs[param.name] = param.default
            else:
                resolved_kwargs[param.name] = builder.resolve(param.annotation)

        if self.factory:
            return self.factory(**resolved_kwargs)
        else:
            return self.typename(**resolved_kwargs)


T = TypeVar("T")


class Builder:
    def __init__(self):
        self._registrations: dict[type, Context] = {}
        self._aliases: dict[type, type] = {}

    def register(
        self,
        cls: type,
        alias: type = None,
        instance: Any = None,
        factory: Callable = None,
        **kwargs,
    ) -> None:
        """Register a type with the builder.

        Args:
            cls: The type to register.
            alias: An optional alias to register the type with.
            instance: An optional instance to register the type with.
            kwargs: Additional keyword arguments to use for resolving the type.
            factory: An optional factory to use for resolving the type.
        """

        context = Context(
            typename=cls,
            aliases={alias} if alias else set(),
            instance=instance,
            factory=factory,
            kwargs=kwargs,
        )

        self._validate(context)
        self._register(context)

    def _resolve_alias(self, alias: type) -> type:
        if alias in self._aliases:
            return self._resolve_alias(self._aliases[alias])

        return alias

    def resolve(self, cls: type[T], **kwargs) -> T:
        """Resolve a type from the builder.

        Args:
            cls: The type to resolve.
            kwargs: Additional keyword arguments to use for resolving the type.
        """
        resolved_type = self._resolve_alias(cls)
        context = self._registrations.get(resolved_type, None)
        if not context:
            raise ResolutionError(f"Unable to resolve type {cls}, no registration found")

        return context.resolve(self, **kwargs)

    def _validate(self, context: Context):
        if context.typename in self._registrations:
            raise RegistrationError(f"Type {context.typename} is already registered")

        if context.typename in self._aliases:
            raise RegistrationError(f"Type {context.typename} is already registered as an alias")

        for alias in context.aliases or set():
            if alias in self._aliases or alias in self._registrations:
                raise RegistrationError(f"Alias {alias} is already registered")

    def _register(self, context: Context) -> None:
        self._registrations[context.typename] = context

        if context.aliases:
            for alias in context.aliases:
                self._aliases[alias] = context.typename

    def __contains__(self, cls: type) -> bool:
        """Check if the builder contains a type or alias."""
        return cls in self._registrations or cls in self._aliases
