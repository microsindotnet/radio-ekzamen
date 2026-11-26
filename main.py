#!/usr/bin/env python3
"""Показ экзаменационных билетов.

Использование:
    python main.py -n=22      # показать билет № 22
    python main.py -r         # показать случайный билет
    python main.py -t         # тест: выбрать режим и пройти случайные билеты до Esc
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

# Множества номеров всех билетов и только сложных (``hard``) билетов.
ALL_NUMBERS = frozenset(t.number for t in tickets.TICKETS)
HARD_NUMBERS = frozenset(t.number for t in tickets.TICKETS if t.hard)

# Режимы теста (как на стартовом экране Vue-версии): код и подпись.
QUIZ_MODES = (
    ("normal", "Обычный тест (случайный выбор билетов)"),
    ("extended", "Расширенный тест (учет статистики ответов)"),
    ("hard", "Только сложные билеты (помеченные как hard)"),
    ("errors", "Повторение ошибок (выдача билетов, где были ошибки)"),
)

# Доля приоритетных ошибочных билетов в режиме "hard" (~2/3).
HARD_ERROR_SHARE = 2 / 3


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


def show_ticket(ticket: tickets.Ticket) -> tuple[bool, bool]:
    """Показать билет, перемешать ответы и проверить выбор.

    Возвращает ``(esc, correct)``: ``esc=True``, если нажат Esc.
    Сложные билеты (``hard``) выводятся жёлтым цветом.
    """
    print("-" * 28)
    if ticket.hard:
        print(f"\033[33mБилет № {ticket.number}\033[0m")
    else:
        print(f"Билет № {ticket.number}")
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
            # «Правильно» зелёным, «, N» (номер ответа) — обычным цветом.
            print("\033[32mПравильно\033[0m" + f", {key}")
        else:
            # «Ошибка» красным, номер ошибочного ответа — обычным цветом,
            # затем правильный ответ.
            print("\033[31mОшибка\033[0m" + f": {key}")
            print(f"Правильный ответ: {correct_text}")
            if ticket.explanation:
                print()
                print(f"Пояснение: {ticket.explanation}")
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


def weighted_choice(items: list[int], weights: list[float]) -> int:
    """Взвешенный выбор одного элемента (аналог ``random.choices(k=1)``)."""
    total = sum(weights)
    r = random.random() * total
    for item, weight in zip(items, weights):
        r -= weight
        if r < 0:
            return item
    return items[-1]


def pick_random(
    excluded: Iterable[int],
    halved: Iterable[int],
    pool: Iterable[int] | None = None,
) -> int:
    """Случайный билет, не входящий в ``excluded``.

    Сложные билеты (``hard``) выпадают в 2 раза чаще, а билеты из ``halved``
    (на которые был дан правильный ответ) — в 2 раза реже. ``pool`` —
    множество номеров, из которых выбираем (по умолчанию все билеты).
    """
    numbers = set(ALL_NUMBERS if pool is None else pool)
    skip = set(excluded)
    half = set(halved)
    all_tickets = [t for t in tickets.TICKETS if t.number in numbers]
    offers = [t for t in all_tickets if t.number not in skip]
    if not offers:  # защита: если исключать стало нечего
        offers = all_tickets
    if not offers:  # защита: пустой пул
        return TICKET_MIN
    population = [t.number for t in offers]
    weights = [
        (2 if t.hard else 1) * (0.5 if t.number in half else 1)
        for t in offers
    ]
    return weighted_choice(population, weights)


def pick_uniform(pool: Iterable[int], excluded: Iterable[int]) -> int:
    """Равновероятный номер из ``pool``, по возможности не из ``excluded``."""
    options = list(pool)
    if not options:  # защита: пустой пул
        return TICKET_MIN
    skip = set(excluded)
    available = [n for n in options if n not in skip]
    if not available:
        available = options
    return available[random.randint(0, len(available) - 1)]


def pick_ticket(
    stats: stat.ErrorStats,
    training: int,
    recent: Iterable[int],
) -> tuple[int, int]:
    """Выбрать следующий билет с учётом счётчика (режим ``extended``).

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
        return pick_random(excluded_random, correct_numbers), training - 1

    # 3. Пора показать билет из списка ошибочных.
    if training == 1:
        if err_numbers:
            candidate = random.choice(err_numbers)
            if candidate not in excluded_recent:
                return candidate, 0
            # Ошибочный билет недавно показывали: показываем обычный,
            # счётчик НЕ уменьшается — повторим попытку позже.
            return pick_random(excluded_random, correct_numbers), 1
        training = 0

    # 4. Ошибочных билетов нет — обычный случайный билет.
    return pick_random(excluded_random, correct_numbers), training


def pick_for_mode(
    mode: str,
    stats: stat.ErrorStats,
    training: int,
    recent: Iterable[int],
) -> tuple[int, int]:
    """Выбрать следующий билет согласно выбранному режиму теста.

    Режимы совпадают с вариантами стартового экрана Vue-версии:

    - ``normal`` — равновероятный случайный билет, статистика не влияет;
    - ``extended`` — расширенный алгоритм (``pick_ticket``) со статистикой;
    - ``hard`` — только сложные билеты, ошибочные выдаются преимущественно
      (~2/3), остальное — случайные сложные;
    - ``errors`` — только билеты из списка ошибочных.
    """
    recent_set = set(recent)
    if mode == "normal":
        return pick_uniform(sorted(ALL_NUMBERS), recent_set), 0
    if mode == "extended":
        return pick_ticket(stats, training, recent)
    if mode == "hard":
        # Ошибочные билеты показываются преимущественно (~2/3), независимо от
        # того, помечены ли они hard; остальное — случайные сложные билеты.
        err_numbers = sorted(stats.counts)
        correct_numbers = set(stats.correct)
        if not err_numbers:
            return pick_random(recent_set, correct_numbers, HARD_NUMBERS), 0
        if random.random() < HARD_ERROR_SHARE:
            options = [n for n in err_numbers if n not in recent_set]
            if not options:
                options = err_numbers
            return options[random.randint(0, len(options) - 1)], 0
        excluded = recent_set | set(err_numbers)
        return pick_random(excluded, correct_numbers, HARD_NUMBERS), 0
    if mode == "errors":
        err_numbers = sorted(stats.counts)
        if not err_numbers:
            return pick_uniform(sorted(ALL_NUMBERS), recent_set), 0
        return pick_uniform(err_numbers, recent_set), 0
    raise ValueError(f"неизвестный режим: {mode}")


def choose_mode() -> str | None:
    """Спросить режим теста. Возвращает код режима или ``None`` при Esc."""
    print("Выберите режим теста:")
    for i, (_, label) in enumerate(QUIZ_MODES, 1):
        print(f"{i}) {label}")
    print()
    while True:
        key = wait_for_key("Режим (1..4) или Esc: ")
        if key == "\x1b":
            if sys.stdin.isatty():
                print()
            return None
        if key in ("1", "2", "3", "4"):
            if sys.stdin.isatty():
                print()
            return QUIZ_MODES[int(key) - 1][0]


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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.num is None and not args.random and not args.test:
        parser.print_help()
        return 0

    stats = stat.ErrorStats(BASE / "err_stat.txt")

    if args.num is not None:
        if not TICKET_MIN <= args.num <= TICKET_MAX:
            parser.error(
                f"номер билета должен быть от {TICKET_MIN} до {TICKET_MAX}"
            )
        esc, ok = show_ticket(tickets.get_ticket(args.num))
        if not esc:
            stats.record(args.num, ok)
        return 0

    if args.random:
        number, _ = pick_ticket(stats, 0, [])
        esc, ok = show_ticket(tickets.get_ticket(number))
        if not esc:
            stats.record(number, ok)
        return 0

    # Режим -t: сначала выбираем режим теста (как стартовый экран Vue-версии).
    mode = choose_mode()
    if mode is None:
        return 0

    training = 0
    # ``recent`` — последние показанные билеты: их не выдаём повторно,
    # пока список не «продвинется» (см. RECENT_LIMIT).
    recent: list[int] = []
    total = 0
    correct = 0
    while True:
        number, training = pick_for_mode(mode, stats, training, recent)
        recent.append(number)
        if len(recent) > RECENT_LIMIT:
            recent.pop(0)
        esc, ok = show_ticket(tickets.get_ticket(number))
        if esc:
            break
        total += 1
        if ok:
            correct += 1
        # В режиме повторения ошибок статистика не ведётся (как в Vue).
        if mode != "errors":
            stats.record(number, ok)
    print_stats(total, correct, total - correct)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
