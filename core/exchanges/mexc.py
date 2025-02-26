from core.exchange import Exchange


class Mexc(Exchange):
    network_param_name = "netWork"

    @property
    def name(self) -> str:
        return "mexc"

    def get_chains_list(self) -> dict:
        """
        MEXC имеет специфическую структуру данных для сетей
        """
        self.exchange.load_markets()
        chains_info = {}
        if self.token in self.exchange.currencies:
            network_list = self.exchange.currencies[self.token]["info"].get("networkList", [])
            for network in network_list:
                if network.get("withdrawEnable"):
                    chains_info[network["network"]] = {
                        "chainId": network["netWork"],
                        "withdrawEnable": True,
                        "withdrawFee": network.get("withdrawFee"),
                        "withdrawMin": network.get("withdrawMin"),
                    }
        return chains_info
