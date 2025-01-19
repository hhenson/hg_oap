"""
1. Aluminum
2. Cocoa
3. Coffee
4. Copper
5. Corn
6. Cotton
7. Crude Oil
8. Gold
9. Lead
10. Lean Hogs
11. Live Cattle
12. Low Sulphur Gas Oil
13. Natural Gas
14. Nickel
15. Platinum
16. RBOB Gasoline
17. Silver
18. Soybean Meal
19. Soybean Oil
20. Soybeans
21. Sugar
22. Tin
23. ULS Diesel
24. Wheat
25. Zinc
"""
from dataclasses import dataclass
from datetime import time, date

from hg_oap.assets.currency import Currency
from hg_oap.dates import Calendar, business_days, roll_bwd, DGen
from hg_oap.impl.assets.currency import Currencies
from hg_oap.impl.instruments.commodity import PhysicalCommodities
from hg_oap.instruments.future import FutureContractSpec, Settlement, SettlementMethod, FutureContractSeries, \
    CONTRACT_BASE_DATE
from hg_oap.instruments.instrument import Instrument
from hg_oap.units import Quantity, Unit
from hg_oap.units.default_unit_system import U
from hg_oap.utils import Expression
from hg_oap.utils.op_declarations import SELF


@dataclass(frozen=True)
class LmeFutureContractSpec(FutureContractSpec):
    """
    Aluminium future contract specification.
    """
    exchange_mic: str = "LME"
    currency: Currency = Currencies.USD.value
    trading_calendar: Calendar = "LME Calendar"
    settlement: Settlement = Settlement(SettlementMethod.Deliverable)
    quotation_currency_unit: Unit = U.USD
    unit_conversion_factors: tuple[Quantity, ...] = lambda self: self.underlying.unit_conversion_factors + (
        self.contract_size / (1.0 * U.lot),
    )


@dataclass(frozen=True)
class BaseMetalFutureContractSpec(LmeFutureContractSpec):
    """
    Base metal future contract specification.
    """
    quotation_unit: Unit = U.USD / U.tonne
    tick_size: Quantity = 0.5 * U.USD / U.tonne


@dataclass(frozen=True)
class AHFutureContractSpec(BaseMetalFutureContractSpec):
    """
    Aluminium future contract specification.
    """
    symbol: str = "AH"
    underlying: Instrument = PhysicalCommodities.AH
    contract_size: Quantity = 25.0 * U.tonne


@dataclass(frozen=True)
class CAFutureContractSpec(BaseMetalFutureContractSpec):
    """
    Cocoa future contract specification.
    """
    symbol: str = "CA"
    underlying: Instrument = PhysicalCommodities.CA
    contract_size: Quantity = 10.0 * U.tonne


@dataclass(frozen=True)
class PBFutureContractSpec(BaseMetalFutureContractSpec):
    """
    Lead future contract specification.
    """
    symbol: str = "PB"
    underlying: Instrument = PhysicalCommodities.PB
    contract_size: Quantity = 25.0 * U.tonne


@dataclass(frozen=True)
class NIFutureContractSpec(BaseMetalFutureContractSpec):
    """
    Nickel future contract specification.
    """
    symbol: str = "NI"
    underlying: Instrument = PhysicalCommodities.NI
    contract_size: Quantity = 6.0 * U.tonne
    tick_size: Quantity = 1.0 * U.USD / U.tonne


@dataclass(frozen=True)
class ZNFutureContractSpec(BaseMetalFutureContractSpec):
    """
    Zinc future contract specification.
    """
    symbol: str = "ZN"
    underlying: Instrument = PhysicalCommodities.ZN
    contract_size: Quantity = 25.0 * U.tonne


@dataclass(frozen=True)
class SNFutureContractSpec(BaseMetalFutureContractSpec):
    """
    Tin future contract specification.
    """
    symbol: str = "SN"
    underlying: Instrument = PhysicalCommodities.SN
    contract_size: Quantity = 5.0 * U.tonne
    tick_size: Quantity = 5.0 * U.USD / U.tonne


@dataclass(frozen=True, kw_only=True)
class LmeFutureContractSeries(FutureContractSeries):
    SELF: "LmeFutureContractSeries" = SELF
    """
    A series of future contracts
    """

    symbol_expr: Expression[[Instrument], str] = lambda \
            future: f"{future.series.spec.symbol}{future.contract_base_date:%Y%m%d}"
    frequency: DGen = business_days  # a date generator that produces the "contract base date" for each future in the series

    first_trading_date: Expression[[date], date] = CONTRACT_BASE_DATE - '3m'  # This depends on contract base date
    last_trading_date: Expression[[date], date] = roll_bwd(CONTRACT_BASE_DATE - '1d').over(
        SELF.spec.trading_calendar)  # When the contract becomes TOM this is the last opportunity to traded. LDN time
    last_trading_time: Expression[[date], date] = time(19, 0)  # Trades to EOD, many brokers may not.

    first_delivery_date: Expression[
        [date], date] = CONTRACT_BASE_DATE  # given a contract base date, produces the first delivery date
    last_delivery_date: Expression[
        [date], date] = CONTRACT_BASE_DATE  # given a contract base date, produces the last delivery date
    expiry: Expression[[date], date] = CONTRACT_BASE_DATE
