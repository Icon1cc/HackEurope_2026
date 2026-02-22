from .base import Tool


class MarketDataTool(Tool):
    name = "market_data"
    description = "Fetch live and historical market/commodity prices"

    def run(self, **kwargs) -> dict:
        # TODO: dispatch to get_spot_price or get_historical based on kwargs
        raise NotImplementedError

    def get_spot_price(self, symbol: str) -> dict:
        # TODO: fetch live spot price for symbol
        raise NotImplementedError

    def get_historical(self, symbol: str, date_range: tuple[str, str]) -> dict:
        # TODO: fetch historical prices for symbol in date range
        raise NotImplementedError
