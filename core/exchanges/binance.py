from core.exchange import Exchange


class Binance(Exchange):
    include_fee_in_params = True
    network_param_name = "network"

    @property
    def name(self) -> str:
        return "binance"

    def _is_withdrawal_enabled(self, key, info):
        return info["info"].get("withdrawEnable")

    def _get_withdraw_fee(self, info):
        return info["info"].get("withdrawFee")
