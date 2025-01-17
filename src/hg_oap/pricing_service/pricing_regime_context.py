from hg_oap.pricing_service import PricingModel, PriceTraits


__all__ = ("PricingRegimeContext",)


class PricingRegimeContext:
    __instance__: ['PricingRegimeContext'] = None

    def __init__(self, name: str, pricing_model_mapping: dict[PriceTraits, PricingModel]):
        self.name = name
        self.pricing_model_mapping = pricing_model_mapping

    @classmethod
    def current(cls) -> 'PricingRegimeContext':
        if not cls.__instance__:
            raise ValueError("No PricingRegimeContext is active")

        return cls.__instance__

    def __enter__(self):
        assert self.__instance__ is None, 'PricingRegimeContext is not stackable'
        self.__class__.__instance__ = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.__instance__ is self
        self.__class__.__instance__ = None

