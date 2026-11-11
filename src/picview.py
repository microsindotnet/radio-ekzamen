"""Отдельный просмотрщик изображений (Tkinter).

Модуль запускается как отдельный процесс, поэтому окно просмотра не
перехватывает фокус у консоли. Окно без рамки, поверх остальных окон,
закрывается при завершении процесса.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__ = ["show", "close"]


def _viewer(path: str) -> None:
    import tkinter as tk

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.title("Просмотр изображения")

    photo = tk.PhotoImage(file=path)
    # уменьшить слишком большие изображения под экран
    max_w = int(root.winfo_screenwidth() * 0.9)
    max_h = int(root.winfo_screenheight() * 0.9)
    if photo.width() > max_w or photo.height() > max_h:
        factor = max(
            1,
            -(-photo.width() // max_w),
            -(-photo.height() // max_h),
        )
        photo = photo.subsample(factor)

    label = tk.Label(root, image=photo, borderwidth=1, relief="solid")
    label.image = photo  # сохранить ссылку
    label.pack()

    root.update_idletasks()
    _, h = root.winfo_width(), root.winfo_height()
    # слева по горизонтали, по центру по вертикали
    x = 0
    y = max(0, (root.winfo_screenheight() - h) // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()


def show(path: Path) -> subprocess.Popen[bytes]:
    """Запустить отдельный процесс просмотрщика для ``path``."""
    return subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def close(proc: subprocess.Popen[bytes] | None) -> None:
    """Закрыть просмотрщик, запущенный ``show``."""
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=2)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


if __name__ == "__main__":
    _viewer(sys.argv[1])
