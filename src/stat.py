"""Статистика ответов (файл ``err_stat.txt``).

Файл состоит из двух разделов:

- ``[Errors]`` — статистика ошибочных ответов: строки ``NNN ошибок K``
  (номер билета, дополненный нулями слева, и количество ошибок);
- ``[Correct]`` — список билетов, на которые был дан правильный ответ:
  по одному номеру в строке.

Пример::

    [Errors]
    090 ошибок 1
    123 ошибок 2

    [Correct]
    005
    020

Списки всегда отсортированы по номеру билета. Разделы ``Errors`` и
``Correct`` не пересекаются: при ошибочном ответе билет удаляется из
``Correct``.

Модуль назван ``stat.py`` по требованию задачи; из-за совпадения имени со
стандартным модулем ``stat`` его следует загружать по пути (см. ``main.py``),
а не обычным ``import stat``.
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["ErrorStats", "WIDTH"]

WIDTH = 3

ERRORS_HEADER = "[Errors]"
CORRECT_HEADER = "[Correct]"


class ErrorStats:
    """Статистика ответов по билетам, хранимая в текстовом файле."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.counts: dict[int, int] = {}
        self.correct: set[int] = set()
        self.load()

    def load(self) -> None:
        """Прочитать статистику из файла.

        Поддерживается и старый формат (без заголовков разделов): тогда все
        строки ``NNN ошибок K`` считаются разделом ``Errors``.
        """
        self.counts = {}
        self.correct = set()
        if not self.path.exists():
            return
        section = "errors"
        for raw in self.path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            low = line.lower()
            if low == ERRORS_HEADER.lower():
                section = "errors"
                continue
            if low == CORRECT_HEADER.lower():
                section = "correct"
                continue
            if section == "correct":
                try:
                    self.correct.add(int(line))
                except ValueError:
                    continue
            else:
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
        """Записать статистику в файл (оба раздела, сортировка по номеру)."""
        lines = [ERRORS_HEADER]
        lines += [
            f"{number:0{WIDTH}d} ошибок {self.counts[number]}"
            for number in sorted(self.counts)
        ]
        lines.append("")
        lines.append(CORRECT_HEADER)
        lines += [f"{number:0{WIDTH}d}" for number in sorted(self.correct)]
        self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def record(self, number: int, correct: bool) -> None:
        """Обновить статистику по ответу на билет ``number``.

        Ошибка увеличивает счётчик ошибок (создаёт строку с 1) и удаляет билет
        из списка ``Correct``. Правильный ответ уменьшает счётчик ошибок
        (при достижении нуля строка удаляется) и добавляет билет в ``Correct``.
        """
        if correct:
            count = self.counts.get(number, 0) - 1
            if count > 0:
                self.counts[number] = count
            else:
                self.counts.pop(number, None)
            self.correct.add(number)
        else:
            self.counts[number] = self.counts.get(number, 0) + 1
            self.correct.discard(number)
        self.save()

    def get(self, number: int) -> int:
        """Текущее число ошибок по билету."""
        return self.counts.get(number, 0)

    def is_correct(self, number: int) -> bool:
        """Был ли по билету правильный ответ (билет в разделе ``Correct``)."""
        return number in self.correct
