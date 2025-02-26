from typing import Tuple, Dict, Type, Optional

from core.exchange import Exchange
from core.exchanges.binance import Binance
from core.exchanges.bybit import Bybit
from core.exchanges.coinex import Coinex
from core.exchanges.gate import Gate
from core.exchanges.huobi import Huobi
from core.exchanges.kucoin import Kucoin
from core.exchanges.mexc import Mexc
from core.exchanges.bitget import Bitget
from core.exchanges.okx import Okx
from core.configes import Config


class ExchangeFactory:
    EXCHANGES: Dict[str, Type[Exchange]] = {
        "binance": Binance,
        "mexc": Mexc,
        "bitget": Bitget,
        "okx": Okx,
        "bybit": Bybit,
        "gate": Gate,
        "kucoin": Kucoin,
        "htx": Huobi,
        "coinex": Coinex
    }

    @staticmethod
    def create(
            exchange_name: str,
            config: Config,
            token: str,
            amount: Tuple[float, float],
            decimal_places: Optional[int] = None,
            address: str = None
    ) -> Exchange:
        """
        Создает экземпляр объекта биржи

        Args:
            exchange_name: Имя биржи
            config: Объект конфигурации
            token: Название токена
            amount: Кортеж (мин. сумма, макс. сумма)
            address: Адрес кошелька

        Returns:
            Объект биржи, реализующий интерфейс Exchange

        Raises:
            ValueError: Если указана неподдерживаемая биржа
        """
        exchange_class = ExchangeFactory.EXCHANGES.get(exchange_name.lower())
        if not exchange_class:
            raise ValueError(
                f"Неподдерживаемая биржа: {exchange_name}"
            )

        return exchange_class(config, token, amount, address, decimal_places)