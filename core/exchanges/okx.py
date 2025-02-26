from core.exchange import Exchange


class Okx(Exchange):
    uses_funding_wallet = True
    include_fee_in_params = True
    
    @property
    def name(self) -> str:
        return "okx"

    def _is_withdrawal_enabled(self, key, info):
        if "info" in info and isinstance(info["info"], dict):
            return info["info"].get("canWd", False)
        return False

    def _get_chain_id(self, key, info):
        return info.get("id")
