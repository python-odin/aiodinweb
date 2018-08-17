from typing import Callable, TypeVar


CV = TypeVar('CV')


class cached_property:  # noqa - Made to match the property builtin
    """
    The bottle cached property, requires a alternate name so as not to
    clash with existing cached_property behaviour
    """
    def __init__(self, func: Callable[[object], CV]) -> None:
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, instance: object, _) -> CV:
        if instance is None:
            return self
        value = instance.__dict__[self.func.__name__] = self.func(instance)
        return value
