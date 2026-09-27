"""Spaced repetition (Leitner boxes), streaks, XP and levels."""
from datetime import date, timedelta

INTERVALS = (0, 1, 3, 7, 16, 35)  # days until next review, indexed by box
MAX_BOX = len(INTERVALS) - 1
LEVEL_XP = 250
DAILY_GOAL = 50


def review(box: int, correct: bool) -> tuple[int, int]:
    """One Leitner step -> (new_box, days_until_due). Wrong answers drop to box 1."""
    box = min(box + 1, MAX_BOX) if correct else 1
    return box, INTERVALS[box]


def xp(correct: bool) -> int:
    return 10 if correct else 2


def level(total_xp: int) -> tuple[int, float]:
    return total_xp // LEVEL_XP + 1, total_xp % LEVEL_XP / LEVEL_XP


def streak(days: set[date], today: date) -> int:
    """Consecutive active days ending today (or yesterday, if today isn't done yet)."""
    d = today if today in days else today - timedelta(1)
    n = 0
    while d in days:
        n += 1
        d -= timedelta(1)
    return n
