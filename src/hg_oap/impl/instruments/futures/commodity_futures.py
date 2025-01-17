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
from hg_oap.assets.currency import Currency
from hg_oap.impl.assets.currency import Currencies
from hg_oap.dates import Calendar, WeekendCalendar
from hg_oap.impl.dates.lme_calendar import LmeExecutionCalendar
from hg_oap.instruments.future import FutureContractSpec, Settlement, SettlementMethod
from hg_oap.instruments.instrument import Instrument
from hg_oap.impl.instruments.commodity import PhysicalCommodities
from hg_oap.units import Quantity, Unit
from hg_oap.units.default_unit_system import U


class Aluminium(FutureContractSpec):
    """
    Aluminium future contract specification.
    """
    exchange_mic: str = "LME"
    symbol: str = "MAL"
    underlying: Instrument = PhysicalCommodities.AH.value
    contract_size: Quantity = Quantity(25., U.ton)
    currency: Currency = Currencies.USD.value
    trading_calendar: Calendar = LmeExecutionCalendar()
    settlement: Settlement = Settlement(SettlementMethod.Deliverable)
    quotation_currency_unit: Unit = U.USD
    quotation_unit: Unit = U.ton
    tick_size: Quantity = Quantity(0.5, U.USD)
    unit_conversion_factors: tuple[Quantity, ...] = lambda self: self.underlying.unit_conversion_factors + (
        self.contract_size / (1.0 * U.lot),
    )