import re
import sys
from enum import Enum
from typing import Tuple

from loguru import logger
import questionary

class WalletType(Enum):
    """Типы кошельков"""
    UNKNOWN = "Неизвестный"
    EVM = "EVM (Ethereum, BSC, Polygon и т.д.)"
    SOLANA = "Solana"
    TRON = "Tron"
    BITCOIN = "Bitcoin"
    RIPPLE = "Ripple (XRP)"
    STELLAR = "Stellar (XLM)"
    TON = "TON"
    COSMOS = "Cosmos"
    POLKADOT = "Polkadot"
    CARDANO = "Cardano"


def setup_logger():
    """
    Настройки логгера и запись в лог
    """
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:DD.MM HH:mm:ss}</green> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logfile.log",
        format="{time:DD.MM HH:mm:ss} | {name} - {message}",
        level="INFO",
        encoding="utf-8"
    )


def is_valid_token_name(
        input_str: str
) -> bool | str:
    """
    Проверка соответствию названия токена
    """
    if re.match(r'^[A-Z]+$', input_str.upper()):
        return True

    return (
        "Название токена должно содержать "
        "только буквы без пробелов и цифр."
    )


def is_valid_number(
        input_str: str,
        min_value: float | None = None
) -> bool | str:
    """
    Проверка соответствию ввода нужного числа
    """
    if not re.match(r'^\d+(\.\d+)?$', input_str):
        return "Введите корректное число (разделитель — точка)."
    value = float(input_str)
    if min_value is not None and value < min_value:
        return f"Значение не может быть меньше {min_value}."

    return True


def count_decimal_places(
        number: float
) -> int:
    """
    Определяет количество знаков после запятой в числе.

    Args:
        number: Число для проверки

    Returns:
        Количество знаков после запятой
    """
    str_num = str(number)
    if '.' not in str_num:
        return 0
    return len(str_num.split('.')[1])


def determine_min_decimals(
        min_amount: float,
        max_amount: float
) -> int:
    """
    Определяет минимальное необходимое количество знаков после запятой
    на основе указанных минимальной и максимальной суммы.

    Args:
        min_amount: Минимальная сумма
        max_amount: Максимальная сумма

    Returns:
        Минимальное количество знаков после запятой
    """
    min_decimals = count_decimal_places(min_amount)
    max_decimals = count_decimal_places(max_amount)

    return max(min_decimals, max_decimals)


def get_max_decimals_for_exchange(
        exchange_name: str
) -> int:
    """
    Возвращает максимальное количество знаков после запятой для биржи.

    Args:
        exchange_name: Название биржи

    Returns:
        Максимальное количество знаков
    """
    # Для Bybit максимум 4 знака, для всех остальных - 6
    if exchange_name.lower() == "bybit":
        return 4
    return 6


def is_valid_decimal_places(
        input_str: str,
        exchange_name: str,
        min_amount: float,
        max_amount: float
) -> bool | str:
    """
    Проверяет, что введенное количество знаков не превышает
    максимально или минимально допустимое для указанной биржи.

    Args:
        input_str: Введенное значение
        exchange_name: Название биржи

    Returns:
        True если значение корректно, иначе строка с ошибкой
    """
    if not re.match(r'^\d+$', input_str):
        return "Введите целое число."

    value = int(input_str)
    if value < 0:
        return (
            "Количество знаков после запятой "
            "не может быть отрицательным."
        )

    max_decimals = get_max_decimals_for_exchange(exchange_name)
    if value > max_decimals:
        return (
            f"Для {exchange_name.upper()} максимальное "
            f"количество знаков после запятой - {max_decimals}."
        )

    min_decimals = determine_min_decimals(min_amount, max_amount)
    if value < min_decimals:
        return (
            f"Минимально необходимое количество "
            f"знаков после запятой - {min_decimals}."
        )

    return True


def is_valid_amount_for_decimals(
        input_str: str,
        exchange_name: str
) -> bool | str:
    """
    Проверяет, что количество знаков после запятой в числе
    не превышает максимально допустимое для биржи.

    Args:
        input_str: Введенное значение
        exchange_name: Название биржи

    Returns:
        True если значение корректно, иначе строка с ошибкой
    """
    if not re.match(r'^\d+(\.\d+)?$', input_str):
        return "Введите корректное число (разделитель — точка)."

    value = float(input_str)
    if value < 0:
        return "Значение должно быть положительным."

    max_decimals = get_max_decimals_for_exchange(exchange_name)
    actual_decimals = count_decimal_places(value)

    if actual_decimals > max_decimals:
        return (
            f"Для {exchange_name.upper()} максимальное "
            f"количество знаков после запятой - {max_decimals}."
        )

    return True

def get_amount_range(
        min_value: float
) -> Tuple[float, float]:
    """
    Запрашивает у пользователя новый диапазон сумм для вывода.

    Args:
        min_value: Минимально допустимое значение

    Returns:
        Tuple[float, float]: Новый диапазон (мин, макс)
    """
    logger.info(
        f"Необходимо задать новый "
        f"диапазон сумм (минимум: {min_value})"
    )

    # Запрашиваем минимальную сумму
    min_amount = questionary.text(
        "Введите новую минимальную сумму:",
        validate=lambda x: is_valid_number(x, min_value)
    ).ask()
    min_amount = float(min_amount)

    # Запрашиваем максимальную сумму
    max_amount = questionary.text(
        "Введите новую максимальную сумму:",
        validate=lambda x: is_valid_number(x, min_amount)
    ).ask()
    max_amount = float(max_amount)

    return min_amount, max_amount


def select_chain(
        chains_list: dict
) -> dict:
    """
    Генерация и вывод списка сетей для выбора пользователем
    """
    available_chains = [
        {
            "name": (
                f"{chain} (ком.: {format_amount(details['withdrawFee'])}, "
                f"мин. сумма: {format_amount(details['withdrawMin'])})"
            ),
            "chainKey": chain,
            "chainId": details["chainId"],
            "withdrawFee": details["withdrawFee"],
            "withdrawMin": details["withdrawMin"],
        }
        for chain, details in chains_list.items()
        if details["withdrawEnable"]
    ]
    if not available_chains:
        logger.error("Нет доступных сетей для вывода!")
        raise ValueError("No available chains")
    choice = questionary.select(
        "Выберите сеть для вывода:",
        choices=[
            {"name": chain["name"],
             "value": chain
             } for chain in available_chains],
    ).ask()
    return choice

def format_amount(n):
    return f"{n:.5f}".rstrip('0').rstrip('.')