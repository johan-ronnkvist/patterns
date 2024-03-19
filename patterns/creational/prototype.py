import copy


class Prototype[T]:
    def clone(self: T) -> T:
        return copy.deepcopy(self)
