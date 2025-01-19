from datetime import date

from hg_oap.dates import months
from hg_oap.impl.instruments.futures.lme import roll_lme


def test_lme_role():
    assert next(("2024-02-01" <= roll_lme(months[3]) )()) == date(2024, 5, 1)