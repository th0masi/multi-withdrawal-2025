from core.exchange import Exchange


class Kucoin(Exchange):
    uses_funding_wallet = True

    @property
    def name(self) -> str:
        return "kucoin"

    def _is_withdrawal_enabled(self, key, info):
        return info["info"].get("withdrawEnable")
