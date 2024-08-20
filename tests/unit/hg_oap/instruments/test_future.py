import sys
from datetime import date

from hg_oap.instruments.physical import PhysicalCommodity
from hg_oap.quanity.conversion import convert_units
from hg_oap.units import Unit
from hg_oap.units.default_unit_system import U
from hgraph import TS, graph, const, WiringGraphContext, getattr_, SCALAR
from hgraph.test import eval_node
from mzar.domain.asset import Power
from mzar.domain.commodities.power.eex.eex_power_future import EEXPowerFuture
from mzar.domain.commodities.power.eex.eex_power_future_contract import EEXPowerFutureContractBaseLoad
from mzar.domain.commodities.power.eex.eex_power_future_series import EEXPowerFutureMonthsSeriesBaseLoad
from mzar.refdata.services.instrument_data_service import instrument_data_by_name
from mzar.refdata.services.refdata_context import RefDataContext
from mzar.refdata.universe.calendars import eex_power_calendar
from mzar.refdata.universe.currencies import Currencies
from test_mzar.pricing.test_utils import register_test_pricing_services

if sys.version_info >= (3, 12):
    from calendar import MARCH
else:
    MARCH = 3

from hg_oap.instruments.future import month_code, month_from_code


def test_month_code():
    assert month_code(MARCH) == 'H'


def test_month_from_code():
    assert month_from_code('H') == MARCH


def test_future_construction():
    spec = EEXPowerFutureContractBaseLoad(
        symbol=f"EEX_DEB",
        underlying=PhysicalCommodity(symbol="DE_POWER_INST", asset=Power(symbol="German Power", name="German Power")),
        currency=Currencies.EUR.value,
        trading_calendar=eex_power_calendar(),
        quotation_unit=U.MWh,
        tick_size=0.01,
        quotation_currency_unit=U.EUR)
    series = EEXPowerFutureMonthsSeriesBaseLoad(spec=spec, months_ahead_trading=6)
    future = EEXPowerFuture(series=series, contract_base_date=date(2024, 8, 14))
    assert future.symbol == "EEX_DEBMQ24"
    assert future.contract_size == 432 * U.MWh


def test_future_unit_conversion():
    @graph
    def g(instrument: TS[str], target_unit: TS[Unit]) -> TS[float]:
        with const(date(2024, 1, 15)) as business_date:
            refdata_service_path = 'refdata'
            instrument_service_path = 'instrument_data'
            with RefDataContext(refdata_service_path=refdata_service_path,
                                instrument_service_path=instrument_service_path):
                register_test_pricing_services()

                instrument = instrument_data_by_name(instrument_service_path, instrument).instrument
                with instrument:
                    multiplier = convert_units(1.0, target_unit, getattr_[SCALAR: Unit](instrument, "unit"))

                WiringGraphContext.instance().build_services()

                return multiplier

    results = eval_node(g, instrument="EEX_DEBMQ24", target_unit=U.lot)
    assert results[-1] == 100.0
