from datetime import date

from hg_oap.dates import months, Tenor
from hg_oap.impl.instruments.futures.lme import roll_lme
from hg_oap.instruments.future import CONTRACT_BASE_DATE


def test_lme_role():
    assert next(("2024-02-01" <= roll_lme(months[3]) )()) == date(2024, 5, 1)