from core.exchange import Exchange


class Gate(Exchange):
    @property
    def name(self) -> str:
        return "gate"

    def _get_chain_id(self, key, info):
        """
        Gate.io использует поле 'id' из информации о сети вместо ключа
        """
        return info.get('id', key)