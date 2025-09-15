from core.exchange import Exchange


class Kucoin(Exchange):
    uses_funding_wallet = True

    @property
    def name(self) -> str:
        return "kucoin"

    def _is_withdrawal_enabled(self, key, info):
        info_dict = info.get("info", {})
        return bool(
            info.get("withdraw", info_dict.get("isWithdrawEnabled",
                   info_dict.get("withdrawEnable", False)))
        )
