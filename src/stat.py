"""Статистика ошибочных ответов (файл ``err_stat.txt``).

Формат строки: ``NNN ошибок K`` — номер билета, дополненный нулями слева,
и количество ошибок по этому билету. Строки хранятся отсортированными
по номеру билета.

Модуль назван ``stat.py`` по требованию задачи; из-за совпадения имени со
стандартным модулем ``stat`` его следует загружать по пути (см. ``main.py``),
а не обычным ``import stat``.
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["ErrorStats", "WIDTH"]

WIDTH = 3


class ErrorStats:
    """Статистика ошибок по билетам, хранимая в текстовом файле."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.counts: dict[int, int] = {}
        self.load()

    def load(self) -> None:
        """Прочитать статистику из файла."""
        self.counts = {}
        if not self.path.exists():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) != 3 or parts[1] != "ошибок":
                continue
            try:
                number = int(parts[0])
                count = int(parts[2])
            except ValueError:
                continue
            if count > 0:
                self.counts[number] = count

    def save(self) -> None:
        """Записать статистику в файл (отсортировано по номеру)."""
        lines = [
            f"{number:0{WIDTH}d} ошибок {self.counts[number]}"
            for number in sorted(self.counts)
        ]
        text = "\n".join(lines)
        if text:
            text += "\n"
        self.path.write_text(text, encoding="utf-8")

    def record(self, number: int, correct: bool) -> None:
        """Обновить статистику по ответу на билет ``number``.

        Ошибка увеличивает счётчик (создаёт строку с 1). Правильный ответ
        уменьшает счётчик; при достижении нуля строка удаляется.
        """
        if correct:
            count = self.counts.get(number, 0) - 1
            if count > 0:
                self.counts[number] = count
            else:
                self.counts.pop(number, None)
        else:
            self.counts[number] = self.counts.get(number, 0) + 1
        self.save()

    def get(self, number: int) -> int:
        """Текущее число ошибок по билету."""
        return self.counts.get(number, 0)
