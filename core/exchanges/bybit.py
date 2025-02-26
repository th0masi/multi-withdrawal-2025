from core.exchange import Exchange


class Bybit(Exchange):
    uses_funding_wallet = True
    max_decimal_places = 4

    @property
    def name(self) -> str:
        return "bybit"
