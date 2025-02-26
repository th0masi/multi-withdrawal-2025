import signal
import sys
import questionary
from loguru import logger

from core.configes import Config
from core.factory import ExchangeFactory
from core.service import WithdrawalService
from core.utils import (
    setup_logger,
    is_valid_token_name,
    is_valid_number,
    determine_min_decimals,
    is_valid_decimal_places, WalletType
)
from core.validator import check_wallets


def signal_handler(sig, frame):
    """
    Обработчик сигнала Ctrl+C
    """
    logger.warning("\n\nРабота софта остановлена пользователем")
    sys.exit(0)


def ask_with_catch(question_func, *args, **kwargs):
    """
    Оборачивает вопросы questionary с обработкой KeyboardInterrupt
    """
    try:
        return question_func(*args, **kwargs).ask()
    except KeyboardInterrupt:
        logger.warning("\n\nРабота софта остановлена пользователем")
        sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)

    setup_logger()
    try:
        config = Config.load()

        # Загрузка и проверка кошельков
        wallets, wallet_type = check_wallets("data/wallets.txt")
        if not wallets:
            logger.error(
                "Кошельки не указаны в data/wallets.txt "
                "или файл недоступен"
                "")
            return

        if not wallet_type or wallet_type == WalletType.UNKNOWN:
            if wallet_type != WalletType.UNKNOWN:
                continue_with_issues = ask_with_catch(
                    questionary.confirm,
                    "Обнаружены проблемы с кошельками. Продолжить выполнение?",
                    default=False
                )
            else:
                continue_with_issues = ask_with_catch(
                    questionary.confirm,
                    "Не смог определить тип кошельков. Продолжить выполнение?",
                    default=False
                )
            if not continue_with_issues:
                logger.info(
                    "Работа программы остановлена пользователем"
                )
                return

        logger.info(f"Загружено кошельков: {len(wallets)}")

        cex_name = questionary.select(
            "Выберите биржу:",
            choices=[
                "Binance", "Mexc", "Okx",
                "Bitget", "Bybit", "Gate",
                "Kucoin", "Htx", "Coinex"
            ]
        ).ask()
        token_name = questionary.text(
            "Название токена:",
            validate=is_valid_token_name
        ).ask()
        min_amount = float(questionary.text(
            "Минимальная сумма:",
            validate=lambda x: is_valid_number(x)
        ).ask())
        max_amount = float(questionary.text(
            "Максимальная сумма:",
            validate=lambda x: is_valid_number(x, min_amount)
        ).ask())

        # Определяем минимально необходимое количество знаков после запятой
        min_decimals = determine_min_decimals(min_amount, max_amount)

        # Запрашиваем максимальное количество знаков после запятой
        max_user_decimals = int(ask_with_catch(
            questionary.text,
            "Максимальное количество знаков после запятой:",
            validate=lambda x: is_valid_decimal_places(x, cex_name, min_amount, max_amount)
        ))

        # Проверяем соответствие указанного количества знаков минимально необходимому
        if max_user_decimals < min_decimals:
            logger.warning(
                f"Указанное количество знаков ({max_user_decimals}) меньше "
                f"минимально необходимого ({min_decimals}) для указанных сумм. "
                f"Будет использовано минимально необходимое количество знаков."
            )

        min_delay = int(questionary.text(
            "Минимальная задержка (сек.):",
            validate=lambda x: is_valid_number(x)
        ).ask())
        max_delay = int(questionary.text(
            "Максимальная задержка (сек.):",
            validate=lambda x: is_valid_number(x, min_delay)
        ).ask())

        try:
            exchange = ExchangeFactory.create(
                cex_name.lower(),
                config,
                token_name,
                (min_amount, max_amount),
                max_user_decimals
            )
            service = WithdrawalService(exchange)
            service.process_withdrawal(
                wallets,
                (min_delay, max_delay)
            )

        except ValueError as e:
            logger.error(f"Ошибка при работе с биржей: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")

    except KeyboardInterrupt:
        logger.warning("\n\nРабота софта остановлена пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

    logger.success("Работа софта завершена")

if __name__ == "__main__":
    main()
