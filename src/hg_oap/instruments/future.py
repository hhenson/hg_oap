from dataclasses import dataclass
from datetime import date, time, datetime
from enum import Enum
from typing import Type

from hg_oap.assets.currency import Currency
from hg_oap.dates.calendar import Calendar
from hg_oap.dates.dgen import DGen, make_dgen
from hg_oap.instruments.instrument import Instrument
from hg_oap.units.default_unit_system import U
from hg_oap.units.quantity import Quantity
from hg_oap.units.unit import Unit
from hg_oap.units.unit_system import UnitConversionContext
from hg_oap.utils import ExprClass, Expression, SELF, ParameterOp
from hg_oap.utils.op import lazy
from hgraph import CompoundScalar

__all__ = (
    "SettlementMethod",
    "Settlement",
    "FutureContractSpec",
    "FutureContractSeries",
    "Future",
    "CONTRACT_BASE_DATE",
    "month_code",
    "month_from_code",
    "MONTH_CODES"
)


class SettlementMethod(Enum):
    Deliverable: str = "Deliverable"
    Financial: str = "Financial"


@dataclass(frozen=True)
class Settlement(CompoundScalar):
    """
    The settlement of a future contract.
    """

    method: SettlementMethod


@dataclass(frozen=True)
class FutureContractSpec(CompoundScalar, ExprClass, UnitConversionContext):
    """
    The specification of a future contract.
    """

    exchange_mic: str
    symbol: str
    underlying: Instrument
    contract_size: Quantity
    currency: Currency

    trading_calendar: Calendar  # Days on which trading happens
    prompt_calendar: Calendar   # Days for which there are delivery contracts

    settlement: Settlement

    quotation_currency_unit: Unit
    quotation_unit: Unit
    tick_size: Quantity
    option_tick_size: Quantity
    option_strike_price_increments: Quantity

    unit_conversion_factors: tuple[Quantity, ...] = lambda self: self.underlying.unit_conversion_factors + (
        self.contract_size / (1.0 * U.lot),
    )


@dataclass(frozen=True, kw_only=True)
class FutureContractSeries(CompoundScalar, ExprClass, UnitConversionContext):
    SELF: "FutureContractSeries" = SELF
    """
    A series of future contracts
    """

    spec: FutureContractSpec
    name: str
    symbol: str = SELF.spec.symbol + SELF.name   # The symbol of the series
    symbol_expr: Expression[[Instrument], str]   # Given a future, generates the symbol for the future
    future_type: Type[Instrument] = lambda self: Future  # The specific type of future belonging to the series
    frequency: DGen  # a date generator that produces the "contract base date" for each future in the series

    first_trading_date: Expression[[date], date]  # given a contract base date, produces the first trading date
    last_trading_date: Expression[[date], date]  # given a contract base date, produces the last trading date
    last_trading_time: time  # NAIVE time of last trading on the last trading date (no timezone)
    trading_timezone: str = "UTC"  # Timezone name for last_trading_time (e.g., "CET", "America/New_York")

    first_delivery_date: Expression[[date], date]  # given a contract base date, produces the first delivery date
    last_delivery_date: Expression[[date], date]  # given a contract base date, produces the last delivery date
    expiry: Expression[[date], date]  # given a contract base date, produces the expiry date

    # default implementations of option expiry dates and times, can be overridden if necessary
    option_first_trading_date: Expression[[date], date] = SELF.first_trading_date
    option_last_trading_date: Expression[[date], date] = SELF.last_trading_date
    option_last_trading_time: time = SELF.last_trading_time
    option_expiry: Expression[[date], date] = SELF.option_last_trading_date
    option_expiry_time: time = SELF.last_trading_time
    option_strike_price_increments: Quantity = SELF.spec.tick_size


CONTRACT_BASE_DATE = lazy(make_dgen)(ParameterOp(_name="CONTRACT_BASE_DATE"))


# Market-convention future month codes for each calendar month
MONTH_CODES = ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"]


def month_code(d: int | date | datetime) -> str:
    # Return the month code corresponding to the month (as a date or a 1-based month number)
    m = (d if d.__class__ is int else d.month) - 1
    return MONTH_CODES[m]


def month_from_code(code: str) -> int:
    # Return a 1-based month number from a month code
    return MONTH_CODES.index(code) + 1


@dataclass(frozen=True, kw_only=True)
class Future(Instrument):
    SELF: "Future" = SELF
    """
    An exchange-tradable instrument with a standardized legal agreement to buy or sell the underlyer at a 
    predetermined price at a specific time in the future.
    """
    series: FutureContractSeries
    contract_base_date: date

    name: str = lambda self: self.series.name + self.contract_base_date.strftime("%b %y")
    symbol: str = SELF.series.symbol_expr(SELF)

    currency_unit: Unit = SELF.series.spec.quotation_currency_unit
    unit: Unit = SELF.series.spec.quotation_unit
    tick_size: Quantity = SELF.series.spec.tick_size

    first_trading_date: date = SELF.series.first_trading_date(CONTRACT_BASE_DATE=SELF.contract_base_date)
    last_trading_date: date = SELF.series.last_trading_date(CONTRACT_BASE_DATE=SELF.contract_base_date)
    last_trading_time: time = SELF.series.last_trading_time  # NAIVE time of last trading (no timezone)
    trading_timezone: str = SELF.series.trading_timezone  # Timezone name for last_trading_time

    first_delivery_date: date = SELF.series.first_delivery_date(CONTRACT_BASE_DATE=SELF.contract_base_date)
    last_delivery_date: date = SELF.series.last_delivery_date(CONTRACT_BASE_DATE=SELF.contract_base_date)
    expiry: date = SELF.series.expiry(CONTRACT_BASE_DATE=SELF.contract_base_date)

    option_first_trading_date: date = SELF.series.option_first_trading_date(CONTRACT_BASE_DATE=SELF.contract_base_date)
    option_last_trading_date: date = SELF.series.option_last_trading_date(CONTRACT_BASE_DATE=SELF.contract_base_date)
    option_last_trading_time: time = SELF.series.option_last_trading_time
    option_expiry: date = SELF.series.option_expiry(CONTRACT_BASE_DATE=SELF.contract_base_date)
    option_expiry_time: time = SELF.series.option_expiry_time
    option_tick_size: Quantity = SELF.series.spec.option_tick_size
    option_strike_price_increments: Quantity = SELF.series.spec.option_strike_price_increments

    unit_conversion_factors: tuple[Quantity, ...] = SELF.series.spec.unit_conversion_factors
    trading_calendar: Calendar = SELF.series.spec.trading_calendar
