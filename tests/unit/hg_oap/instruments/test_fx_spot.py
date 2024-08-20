from mzar.domain.instruments.fx import FXSpot
from mzar.refdata.universe.currencies import Currencies


def test_fx_spot_symbol():
    assert FXSpot(base=Currencies.GBP.value, quote=Currencies.JPY.value).symbol == 'GBPJPY.SPOT'