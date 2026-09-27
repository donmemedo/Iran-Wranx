from datetime import date, timedelta

import srs


def test_srs():
    assert srs.review(0, True) == (1, 1)
    assert srs.review(4, True) == (5, 35)
    assert srs.review(5, True) == (5, 35)  # capped
    assert srs.review(5, False) == (1, 1)
    t = date(2026, 9, 23)
    d = lambda n: t - timedelta(n)
    assert srs.streak(set(), t) == 0
    assert srs.streak({d(1), d(2)}, t) == 2  # today not done yet
    assert srs.streak({d(0), d(1), d(3)}, t) == 2  # gap breaks it
    assert srs.level(0) == (1, 0) and srs.level(260) == (2, 10 / 250)


if __name__ == "__main__":
    test_srs()
    print("ok")
