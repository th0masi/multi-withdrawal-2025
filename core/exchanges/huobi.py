from typing import Dict
from loguru import logger

from core.exchange import Exchange


class Huobi(Exchange):
    @property
    def name(self) -> str:
        return "htx"

    def get_chains_list(self) -> Dict:
        """
        Huobi (HTX) имеет свою структуру данных для сетей
        """
        logger.info("Получаю данные о сетях для вывода...")
        self.exchange.load_markets()
        chains_info = {}

        if self.token in self.exchange.currencies:
            networks = self.exchange.currencies[self.token].get("networks", {})
            for key, info in networks.items():
                if info.get("withdraw", False):
                    chains_info[key] = {
                        "chainId": info.get("id", key),
                        "withdrawEnable": True,
                        "withdrawFee": info.get("fee"),
                        "withdrawMin": info.get("limits", {}).get("withdraw", {}).get("min"),
                    }

        return chains_info
