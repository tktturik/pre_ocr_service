from collections.abc import Iterable


class Registry[T]:
    """Реестр именованных элементов одного вида с сохранением порядка регистрации."""

    def __init__(self, kind: str) -> None:
        self._kind = kind
        self._items: dict[str, T] = {}

    def register(self, name: str, item: T) -> None:
        """Регистрирует элемент; повторное имя `ValueError` (ошибка сборки, не запроса)."""
        if name in self._items:
            raise ValueError(f"{self._kind} '{name}' is already registered")
        self._items[name] = item

    def get(self, name: str) -> T:
        """Возвращает элемент по имени; неизвестное имя `KeyError`."""
        return self._items[name]

    def names(self) -> tuple[str, ...]:
        """Имена элементов в порядке регистрации."""
        return tuple(self._items)

    def unknown(self, names: Iterable[str]) -> tuple[str, ...]:
        """Имена из запроса, которых нет в реестре, в порядке запроса."""
        return tuple(name for name in names if name not in self._items)
