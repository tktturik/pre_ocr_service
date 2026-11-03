from core.errors import OverloadedError


class AdmissionLimiter:
    """Счётчик слотов лимита входа: занято running + waiting, сверх — перегрузка.

    Без блокировок: работает только в цикле событий. Слот освобождается
    колбэком завершения future pebble, а не в обработчике запроса.
    """

    def __init__(self, running: int, waiting: int) -> None:
        self._capacity = running + waiting
        self._occupied = 0

    def acquire(self) -> None:
        """Занимает слот; при исчерпанном лимите сразу `OverloadedError`."""
        if self._occupied >= self._capacity:
            raise OverloadedError("overloaded")
        self._occupied += 1

    def release(self) -> None:
        """Освобождает слот, занятый через `acquire`."""
        self._occupied -= 1
