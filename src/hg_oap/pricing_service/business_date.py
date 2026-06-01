from datetime import date

from hgraph import reference_service, TS


__all__ = ("current_business_date",)


@reference_service
def current_business_date(path: str = "current_business_date") -> TS[date]:
    """
    Streams the current business date for today
    """
