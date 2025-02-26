from typing import List, Tuple, Dict
from core.exchange import Exchange
from core.utils import select_chain, get_amount_range
from loguru import logger
import random
import time


class WithdrawalService:
    """
    Сервис для обработки вывода средств с бирж
    """

    def __init__(self, exchange: Exchange):
        self.exchange = exchange

    def process_withdrawal(
            self,
            wallet_list: List[str],
            delay: Tuple[float, float],
            skip_failed: bool = True
    ) -> Dict[str, bool]:
        """
        Обрабатывает вывод средств на список кошельков

        Args:
            wallet_list: Список адресов кошельков
            delay: Кортеж (мин. задержка, макс. задержка) в секундах
            skip_failed: Пропускать ли кошельки при неудачных выводах

        Returns:
            Словарь с результатами выводов: {адрес: успешно}
        """
        results = {}

        try:
            # Проверка авторизации и баланса
            self._prepare_withdrawal(wallet_list)

            # Получаем и выбираем сеть для вывода
            chains_list = self.exchange.get_chains_list()
            if not chains_list:
                logger.error(
                    f"Для токена {self.exchange.token} не "
                    f"найдены доступные сети на {self.exchange.name}"
                )
                return results

            selected_chain = select_chain(chains_list)

            # Корректируем минимальную сумму вывода при необходимости
            self._adjust_amount_if_needed(selected_chain)

            # Выполняем вывод для каждого кошелька
            for wallet in wallet_list:
                self.exchange.address = wallet
                success = self.exchange.withdraw(selected_chain)
                results[wallet] = success

                # Если вывод не удался и skip_failed=True, пропускаем задержку
                if not success and skip_failed:
                    continue

                # Задержка между выводами
                if wallet != wallet_list[-1]:  # Если это не последний кошелек
                    self._sleep_between_withdrawals(delay)

            return results

        except Exception as e:
            logger.error(
                f"Ошибка при работе с "
                f"{self.exchange.name.upper()}: {e}"
            )
            return results

    def _prepare_withdrawal(self, wallet_list: List[str]) -> None:
        """
        Подготовка к выводу: проверка авторизации и баланса
        """
        self.exchange.check_auth()
        logger.info("Проверяю баланс...")
        self.exchange.get_balance(len(wallet_list))

    def _adjust_amount_if_needed(self, selected_chain: Dict) -> None:
        """
        Корректировка минимальной суммы вывода, если требуется
        """
        min_withdraw = float(selected_chain["withdrawMin"])
        if min_withdraw > self.exchange.min_amount:
            logger.warning(
                f"Указанная мин. сумма "
                f"{self.exchange.min_amount} меньше, "
                f"чем на {self.exchange.name.upper()}: "
                f"{min_withdraw}"
            )

            # Запрашиваем новый диапазон сумм
            new_min, new_max = get_amount_range(min_withdraw)
            self.exchange.min_amount = new_min
            self.exchange.max_amount = new_max
            logger.info(
                f"Установлены новые значения: "
                f"мин. {new_min}, макс. {new_max} "
                f"${self.exchange.token}"
            )

    @staticmethod
    def _sleep_between_withdrawals(delay: Tuple[float, float]) -> None:
        """
        Задержка между выводами средств
        """
        sleep_time = random.randint(*delay)
        logger.info(
            f"Сплю {sleep_time} сек. "
            f"перед следующим кошельком..."
        )
        time.sleep(sleep_time)