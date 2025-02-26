from loguru import logger

from core.exchange import Exchange


class Coinex(Exchange):
    include_fee_in_params = True

    @property
    def name(self) -> str:
        return "coinex"

    def _is_withdrawal_enabled(self, key, info):
        return info["info"].get("withdrawEnable")

    def _get_withdraw_fee(self, info):
        return info["info"].get("withdrawFee")

    def get_chains_list(self) -> dict:
        """
        Coinex имеет специфическую структуру данных для сетей
        """
        logger.info("Получаю данные о сетях для вывода Coinex...")
        self.exchange.load_markets()
        chains_info = {}

        if self.token in self.exchange.currencies:
            currency_data = self.exchange.currencies[self.token]

            if "info" in currency_data and "chains" in currency_data["info"]:
                chains = currency_data["info"]["chains"]

                for chain_info in chains:
                    chain_id = chain_info.get("chain")
                    withdraw_enabled = chain_info.get("withdraw_enabled", False)

                    if chain_id and withdraw_enabled:
                        chains_info[chain_id] = {
                            "chainId": chain_id,
                            "withdrawEnable": True,
                            "withdrawFee": float(chain_info.get("withdrawal_fee", 0)),
                            "withdrawMin": float(chain_info.get("min_withdraw_amount", 0)),
                        }

        return chains_info
