from core.exchange import Exchange


class Bitget(Exchange):
    network_param_name = "network"

    @property
    def name(self) -> str:
        return "bitget"

    def _is_withdrawal_enabled(self, key, info):
        return info.get("info", {}).get("withdrawable", "false") == "true"

    def _get_withdraw_fee(self, info):
        return info["info"].get("withdrawFee")
