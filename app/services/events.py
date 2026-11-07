import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class BudgetExceededEvent:
    """Подія «місячний бюджет перевищено»."""

    year: int
    month: int
    limit: float
    spent: float

    @property
    def overspent(self) -> float:
        return self.spent - self.limit


class BudgetObserver(ABC):
    """Спостерігач (патерн Observer): реагує на перевищення бюджету."""

    @abstractmethod
    def update(self, event: BudgetExceededEvent) -> None:
        pass


class BudgetSubject:
    """Суб'єкт (патерн Observer): зберігає спостерігачів і сповіщає їх."""

    def __init__(self) -> None:
        self._observers: List[BudgetObserver] = []

    def attach(self, observer: BudgetObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: BudgetObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event: BudgetExceededEvent) -> None:
        for observer in list(self._observers):
            observer.update(event)


class LoggingBudgetObserver(BudgetObserver):
    """Записує попередження про перевищення бюджету в журнал."""

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def update(self, event: BudgetExceededEvent) -> None:
        self._logger.warning(
            "Бюджет за %02d.%d перевищено на %.2f",
            event.month, event.year, event.overspent,
        )


class MessageBudgetObserver(BudgetObserver):
    """Накопичує тексти попереджень, щоб контролер показав їх користувачу."""

    def __init__(self) -> None:
        self._messages: List[str] = []

    def update(self, event: BudgetExceededEvent) -> None:
        self._messages.append(
            f"Бюджет за {event.month:02d}.{event.year} перевищено на "
            f"{event.overspent:.2f} ₴"
        )

    def pop_messages(self) -> List[str]:
        messages = list(self._messages)
        self._messages.clear()
        return messages
