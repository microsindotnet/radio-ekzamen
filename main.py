#!/usr/bin/env python3
"""Показ экзаменационных билетов.

Использование:
    python main.py -n=22      # показать билет № 22
    python main.py -r         # показать случайный билет
    python main.py -t         # тест: случайные билеты до нажатия Esc
    python main.py -t -e      # тест, сложные билеты в 2 раза чаще
    python main.py -h         # подсказка
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import random
import sys
from collections.abc import Iterable
from pathlib import Path

# Позволяет запускать как `python main.py` из корня проекта,
# так и `python src/main.py`.
BASE = Path(__file__).resolve().parent
SRC = BASE / "src" if (BASE / "src").is_dir() else BASE
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import answers  # noqa: E402
import picview  # noqa: E402
import tickets  # noqa: E402


def _load_stat_module():
    # имя `stat` конфликтует со стандартным модулем Python,
    # поэтому загружаем src/stat.py по пути
    spec = importlib.util.spec_from_file_location("err_stat", SRC / "stat.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stat = _load_stat_module()

TICKET_MIN = 1
TICKET_MAX = 426

# Сколько последних показанных билетов исключать из случайного выбора, чтобы
# один и тот же билет не выпадал слишком часто.
RECENT_LIMIT = 10


def wait_for_key(prompt: str = "Выберите ответ (1..4) или Esc: ") -> str:
    """Ждать нажатия клавиши и вернуть её."""
    if sys.stdin.isatty():
        # вернуться в начало строки и перерисовать запрос
        print("\r\033[K" + prompt, end="", flush=True)
        if os.name == "nt":
            import msvcrt

            return msvcrt.getch().decode("utf-8", "ignore")
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    key = input(prompt)[:1]
    print()
    return key


def show_ticket(ticket: tickets.Ticket, extend: bool = False) -> tuple[bool, bool]:
    """Показать билет, перемешать ответы и проверить выбор.

    Возвращает ``(esc, correct)``: ``esc=True``, если нажат Esc.
    При ``extend=True`` заголовок билета выводится жёлтым цветом.
    """
    print("-" * 28)
    if extend and ticket.hard:
        print(f"\033[33mБилет № {ticket.number}\033[0m")
    else:
        print(f"Билет № {ticket.number}")
    print()
    print("Вопрос:")
    print(ticket.question)
    print()

    image_proc = None
    if ticket.image:
        image_path = tickets.MEDIA_DIR / ticket.image
        # print(f"Картинка: {ticket.image}")
        image_proc = picview.show(image_path)

    choices = list(zip("abcd", ticket.answers))
    random.shuffle(choices)
    for i, (_, text) in enumerate(choices, 1):
        print(f"{i}) {text}")
    print()

    correct_letter = answers.ANSWERS[ticket.number]
    correct_text = ticket.answers["abcd".index(correct_letter)]

    try:
        while True:
            key = wait_for_key()
            picview.close(image_proc)
            image_proc = None

            if key == "\x1b":
                if sys.stdin.isatty():
                    print()
                return (True, False)
            if key in ("1", "2", "3", "4"):
                break

        selected_letter = choices[int(key) - 1][0]
        correct = selected_letter == correct_letter
        if correct:
            print("\033[32mПравильно\033[0m")
        else:
            print("\033[31mОшибка\033[0m")
            print(f"Правильный ответ: {correct_text}")
        return (False, correct)
    finally:
        picview.close(image_proc)


def print_stats(total: int, correct: int, wrong: int) -> None:
    """Вывести статистику в рамке."""
    line1 = f"Пройдено вопросов: {total}"
    line2 = f"Из них верно: {correct}"
    line3 = f"Ошибок: {wrong}"
    width = max(len(line1), len(line2), len(line3))
    border = "+" + "-" * (width + 2) + "+"
    print(border)
    print("| " + line1.ljust(width) + " |")
    print("| Из них верно: " + "\033[32m" + str(correct) + "\033[0m" + " " * (width - len(line2)) + " |")
    print("| Ошибок: " + "\033[31m" + str(wrong) + "\033[0m" + " " * (width - len(line3)) + " |")
    print(border)


def pick_random(
    extend: bool = False,
    excluded: Iterable[int] | None = None,
    halved: Iterable[int] | None = None,
) -> int:
    """Случайный номер билета, которого нет в ``excluded``.

    При ``extend=True`` сложные билеты (``hard``) выпадают в 2 раза чаще.
    ``excluded`` — номера, которые нельзя выдавать (последние показанные
    билеты и ошибочные билеты). ``halved`` — билеты, на которые был дан
    правильный ответ (раздел ``Correct``): они выпадают в 2 раза реже.
    """
    skip = set(excluded or ())
    half = set(halved or ())
    if extend:
        offers = [t for t in tickets.TICKETS if t.number not in skip]
        if not offers:  # защита: если исключать стало нечего
            offers = list(tickets.TICKETS)
        population = [t.number for t in offers]
        weights = [
            (2 if t.hard else 1) * (0.5 if t.number in half else 1)
            for t in offers
        ]
        return random.choices(population, weights=weights, k=1)[0]
    while True:
        number = random.randint(TICKET_MIN, TICKET_MAX)
        if number in skip:
            continue
        if number in half and random.random() < 0.5:
            continue
        return number


def pick_ticket(
    extend: bool,
    stats: stat.ErrorStats,
    training: int,
    recent: list[int],
) -> tuple[int, int]:
    """Выбрать следующий билет с учётом тренировочного счётчика.

    ``training`` — счётчик «тренировки». ``recent`` — последние показанные
    билеты (не длиннее ``RECENT_LIMIT``); их нельзя вытянуть случайно, чтобы
    недавние билеты не повторялись подряд.

    Алгоритм:

    1. Счётчик равен 0 и есть ошибочные билеты — заводим отсчёт
       ``RECENT_LIMIT + G``, где ``G`` — случайное число 5..10. То есть
       ошибочный билет повторяется не раньше, чем через ``10 + G`` вопросов.
    2. Счётчик больше 1 — показываем обычный случайный билет (кроме ``recent``
       и ошибочных; сложные ``hard`` — в 2 раза чаще, а билеты из раздела
       ``Correct`` — в 2 раза реже), счётчик уменьшается на 1.
    3. Счётчик равен 1 — показываем случайный билет из списка ошибочных. Если
       он не входит в ``recent``, счётчик сбрасывается в 0; если входит, то
       показываем обычный случайный билет, а счётчик НЕ уменьшается, чтобы
       повторить попытку позже.
    4. Ошибочных билетов нет — обычный случайный билет.

    Возвращает ``(number, training)`` — номер билета и новое значение счётчика.
    """
    err_numbers = sorted(stats.counts)
    # Билеты с правильным ответом (раздел Correct) выпадают в 2 раза реже.
    correct_numbers = set(stats.correct)
    excluded_recent = set(recent)
    # Обычный случайный выбор исключает и последние показанные билеты, и все
    # ошибочные. Ошибочные показываются ТОЛЬКО счётчиком training, поэтому
    # повтор происходит строго не раньше, чем через RECENT_LIMIT + G вопросов.
    excluded_random = excluded_recent | set(err_numbers)

    # 1. Счётчик не активен, но есть ошибочные билеты — новый отсчёт.
    #    Повтор ошибочного билета — не раньше, чем через RECENT_LIMIT + G
    #    вопросов (G случайно 5..10).
    if training == 0 and err_numbers:
        training = RECENT_LIMIT + random.randint(5, 10)

    # 2. Обычный случайный билет (не recent, не ошибочный), счётчик -1.
    if training > 1:
        return pick_random(extend, excluded_random, correct_numbers), training - 1

    # 3. Пора показать билет из списка ошибочных.
    if training == 1:
        if err_numbers:
            candidate = random.choice(err_numbers)
            if candidate not in excluded_recent:
                return candidate, 0
            # Ошибочный билет недавно показывали: показываем обычный,
            # счётчик НЕ уменьшается — повторим попытку позже.
            return pick_random(extend, excluded_random, correct_numbers), 1
        training = 0

    # 4. Ошибочных билетов нет — обычный случайный билет.
    return pick_random(extend, excluded_random, correct_numbers), training


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Показ экзаменационных билетов.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-n",
        "--num",
        type=int,
        metavar="N",
        help=f"номер билета {TICKET_MIN}..{TICKET_MAX}",
    )
    group.add_argument(
        "-r",
        "--random",
        action="store_true",
        help="случайный билет",
    )
    group.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="тест: случайные билеты до нажатия Esc",
    )
    parser.add_argument(
        "-e",
        "--extend",
        action="store_true",
        help="сложные билеты предлагать в 2 раза чаще",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.num is None and not args.random and not args.test:
        parser.print_help()
        return 0

    stats = stat.ErrorStats(BASE / "err_stat.txt")
    training = 0

    if args.num is not None:
        if not TICKET_MIN <= args.num <= TICKET_MAX:
            parser.error(
                f"номер билета должен быть от {TICKET_MIN} до {TICKET_MAX}"
            )
        esc, ok = show_ticket(tickets.get_ticket(args.num), args.extend)
        if not esc:
            stats.record(args.num, ok)
        return 0

    if args.random:
        number, training = pick_ticket(args.extend, stats, training, [])
        esc, ok = show_ticket(tickets.get_ticket(number), args.extend)
        if not esc:
            stats.record(number, ok)
        return 0

    # ``recent`` — последние показанные билеты: их не выдаём повторно,
    # пока список не «продвинется» (см. RECENT_LIMIT).
    recent: list[int] = []
    total = 0
    correct = 0
    while True:
        number, training = pick_ticket(args.extend, stats, training, recent)
        recent.append(number)
        if len(recent) > RECENT_LIMIT:
            recent.pop(0)
        esc, ok = show_ticket(tickets.get_ticket(number), args.extend)
        if esc:
            break
        total += 1
        if ok:
            correct += 1
        stats.record(number, ok)
    print_stats(total, correct, total - correct)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
