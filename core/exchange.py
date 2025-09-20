import random
import ccxt

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from loguru import logger

from core.configes import Config


class Exchange(ABC):
    uses_funding_wallet = False
    network_param_name = "chain"
    include_fee_in_params = False
    requires_password = False
    requires_api_password = False
    max_decimal_places = 6

    def __init__(
            self,
            config: Config,
            token: str,
            amount: Tuple[float, float],
            address: str = None,
            decimal_places: Optional[int] = None
    ):
        self.config = config
        self.token = token.upper()
        self.min_amount, self.max_amount = amount
        self.address = address

        if decimal_places is not None and decimal_places <= self.max_decimal_places:
            self.decimal_places = decimal_places
        else:
            self.decimal_places = self.max_decimal_places

        if not self._validate_auth_config():
            raise ValueError(
                f"Не настроена аутентификация "
                f"для биржи {self.name.upper()}"
            )

        self.exchange = self._initialize_exchange()

    def _validate_auth_config(self) -> bool:
        """
        Проверяет наличие и валидность настроек аутентификации для биржи
        """
        try:
            exchange_config = getattr(self.config.settings, self.name)

            # Проверяем API ключ и секрет
            if not exchange_config.api_key or exchange_config.api_key == "YOUR_API_KEY_HERE":
                logger.error(
                    f"API ключ для {self.name.upper()} не "
                    f"настроен в конфигурации"
                )
                return False

            if not exchange_config.api_secret or exchange_config.api_secret == "YOUR_API_SECRET_HERE":
                logger.error(
                    f"API секрет для {self.name.upper()} "
                    f"не настроен в конфигурации"
                )
                return False

            # Проверяем пароль для API, если он требуется
            if self.requires_api_password:
                if not hasattr(exchange_config, "password") or not exchange_config.password:
                    logger.error(
                        f"API пароль для {self.name.upper()} "
                        f"не настроен в конфигурации"
                    )
                    return False

            return True

        except AttributeError:
            logger.error(
                f"Настройки для биржи {self.name.upper()} "
                f"не найдены в конфигурации"
            )
            return False

    def _initialize_exchange(self) -> ccxt.Exchange:
        """
        Инициализирует объект биржи
        """
        exchange_config = getattr(self.config.settings, self.name)

        options: Dict[str, Any] = {
            "apiKey": exchange_config.api_key,
            "secret": exchange_config.api_secret,
            "enableRateLimit": True,
        }

        # Если биржа использует funding кошелек
        if self.uses_funding_wallet:
            options["options"] = {
                "defaultType": "funding",
                "accountsByType": {
                    "spot": "trade",
                    "funding": "main"
                }
            }
        else:
            options["options"] = {"defaultType": "spot"}

        if hasattr(exchange_config, "password") and exchange_config.password:
            options["password"] = exchange_config.password

        return getattr(ccxt, self.name)(options)

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def get_chains_list(self) -> Dict:
        """
        Получение списка сетей для вывода.
        """
        logger.info("Получаю данные о сетях для вывода...")
        self.exchange.load_markets()
        chains_info = {}

        if self.token in self.exchange.currencies:
            networks = self.exchange.currencies[self.token].get("networks", {})
            for key, info in networks.items():
                withdraw_fee = float(self._get_withdraw_fee(info) or 0)
                withdraw_min = float(self._get_withdraw_min(info) or 0)

                if self._is_withdrawal_enabled(key, info):
                    chains_info[key] = {
                        "chainId": self._get_chain_id(key, info),
                        "withdrawEnable": True,
                        "withdrawFee": withdraw_fee,
                        "withdrawMin": withdraw_min,
                    }
        return chains_info

    def _is_withdrawal_enabled(self, key, info) -> bool:
        """
        Проверка доступности вывода для конкретной сети.
        """
        return info.get("withdraw", True)

    def _get_chain_id(self, key, info) -> str:
        """
        Получение ID сети.
        """
        return info.get('id', key)

    def _get_withdraw_fee(self, info) -> Optional[float]:
        """
        Получение комиссии за вывод.
        """
        return info.get("fee")

    @staticmethod
    def _get_withdraw_min(info) -> Optional[float]:
        """
        Получение минимальной суммы для вывода.
        """
        return info.get("limits", {}).get("withdraw", {}).get("min")

    def get_balance(self, num_wallets: int) -> float:
        """
        Получение баланса.
        """
        balances = self._fetch_balance()
        balance = float(balances.get("total", {}).get(self.token, 0))
        from core.utils import format_amount
        logger.success(
            f"Баланс токена: {format_amount(balance)} ${self.token}"
        )
        self._check_enough_balance(balance, num_wallets)
        return balance

    def _fetch_balance(self):
        """
        Получение баланса с биржи.
        """
        # Для бирж, которые требуют параметр типа кошелька
        if self.uses_funding_wallet:
            return self.exchange.fetch_balance({"type": "funding"})
        return self.exchange.fetch_balance()

    def _generate_random_amount(self) -> float:
        """
        Генерирует случайную сумму для вывода с учетом указанного
        количества знаков после запятой.
        """
        # Получаем базовое случайное значение
        amount = random.uniform(self.min_amount, self.max_amount)

        # Определяем минимальное количество знаков после запятой
        # на основе указанных min_amount и max_amount
        from core.utils import determine_min_decimals
        min_decimals = determine_min_decimals(self.min_amount, self.max_amount)

        # Если пользователь указал не меньше минимально необходимого
        if self.decimal_places >= min_decimals:
            # Если разрешено использовать различное количество знаков,
            # выбираем случайное число от минимального до максимального
            if min_decimals < self.decimal_places:
                decimals = random.randint(min_decimals, self.decimal_places)
            else:
                decimals = min_decimals
        else:
            # Если пользователь указал меньше минимально необходимого,
            # используем минимально необходимое количество знаков
            decimals = min_decimals
            logger.warning(
                f"Используется минимально необходимое "
                f"количество знаков: {decimals}"
            )

        # Округляем до нужного количества знаков
        rounded_amount = round(amount, decimals)
        logger.debug(
            f"Сгенерирована сумма {rounded_amount} "
            f"({decimals} знаков после запятой)"
        )

        return rounded_amount

    def withdraw(self, chain: Dict) -> bool:
        """
        Универсальный метод вывода средств.
        """
        amount = self._generate_random_amount()

        try:
            # Подготовка параметров в зависимости от биржи
            params = {
                self.network_param_name: chain["chainId"],
            }

            # Добавляем комиссию, если требуется для конкретной биржи
            if hasattr(self, 'include_fee_in_params') and self.include_fee_in_params:
                params["fee"] = chain["withdrawFee"]

            # Добавляем пароль (для некоторых бирж)
            if hasattr(self, 'requires_password') and self.requires_password:
                params["pwd"] = "-"

            withdrawal = self.exchange.withdraw(
                self.token,
                amount,
                self.address,
                params=params,
            )
            withdrawal_id = self._extract_withdrawal_id(withdrawal)
            if withdrawal_id:
                logger.success(
                    f"{self.address} | Запрос на "
                    f"вывод {amount} ${self.token}, "
                    f"ID: {withdrawal_id}"
                )
                return True
        except Exception as e:
            logger.error(
                f"{self.address} | Ошибка "
                f"вывода {amount} ${self.token}: {e}"
            )
            return False

    def _check_enough_balance(
            self, balance: float, num_wallets: int
    ) -> bool:
        avg_amount = (self.min_amount + self.max_amount) / 2
        if balance < num_wallets * self.min_amount:
            logger.error(
                f"Баланса недостаточно для "
                f"вывода на {num_wallets} кошельков"
            )
            raise ValueError("Недостаточно средств")
        if balance < num_wallets * avg_amount:
            logger.warning(
                f"Возможно, баланса не хватит "
                f"для вывода на {num_wallets} кошельков"
            )
            return False

        return True

    def check_auth(self) -> None:
        logger.info("Тестирую авторизацию...")
        try:
            self.exchange.fetch_balance()
            logger.success("Успешная авторизация")
        except ccxt.AuthenticationError as e:
            logger.error(f"Ошибка авторизации: {e}")
            raise

    @staticmethod
    def _extract_withdrawal_id(withdrawal: Dict) -> str:
        return withdrawal.get("id", withdrawal.get("info", {}).get("wdId", ""))

