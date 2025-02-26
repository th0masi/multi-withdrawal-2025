import re
from typing import List, Tuple, Optional
from loguru import logger

from core.utils import WalletType


class WalletValidator:
    """Класс для проверки и автоопределения типа кошельков"""

    WALLET_PATTERNS = {
        WalletType.EVM: r'^0x[a-fA-F0-9]{40}$',
        WalletType.SOLANA: r'^[1-9A-HJ-NP-Za-km-z]{43,44}$',
        WalletType.TRON: r'^T[A-Za-z0-9]{33}$',
        WalletType.BITCOIN: r'^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}$',
        WalletType.RIPPLE: r'^r[0-9a-zA-Z]{24,34}$',
        WalletType.STELLAR: r'^G[A-Z0-9]{55}$',
        WalletType.TON: r'^UQ[a-zA-Z0-9_-]{46}$|^EQ[a-zA-Z0-9_-]{46}$',
        WalletType.COSMOS: r'^cosmos[0-9a-z]{38,42}$',
        WalletType.POLKADOT: r'^[1-9A-HJ-NP-Za-km-z]{47,48}$',
        WalletType.CARDANO: r'^addr1[a-zA-Z0-9]{30,120}$'
    }

    PRIVATE_KEY_LENGTHS = {
        WalletType.EVM: 64,  # 64 символа (без 0x)
    }

    def __init__(self, wallets: List[str]):
        """
        Инициализирует проверку кошельков

        Args:
            wallets: Список адресов кошельков для проверки
        """
        self.wallets = wallets
        self.wallet_type = WalletType.UNKNOWN
        self.standard_length = 0

    def validate(self) -> bool:
        """
        Проверяет список кошельков на соответствие требованиям

        Returns:
            True если все кошельки корректны, иначе False
        """
        if not self.wallets:
            logger.error("Список кошельков пуст!")
            return False

        result = self._check_length_and_determine_type()
        if not result:
            return False

        if self.wallet_type == WalletType.EVM:
            self._check_for_private_keys()

        return True

    def _check_length_and_determine_type(self) -> bool:
        """
        Проверяет одинаковую длину всех кошельков и определяет их тип

        Returns:
            True если все кошельки имеют одинаковую длину, иначе False
        """
        length_counts = {}
        for wallet in self.wallets:
            wallet = wallet.strip()
            length = len(wallet)
            length_counts[length] = length_counts.get(length, 0) + 1

        # Находим наиболее частую длину
        common_length, common_count = max(length_counts.items(), key=lambda x: x[1])
        self.standard_length = common_length

        # Проверяем все кошельки на соответствие стандартной длине
        non_standard_wallets = []
        for i, wallet in enumerate(self.wallets):
            wallet = wallet.strip()
            if len(wallet) != common_length:
                non_standard_wallets.append((i + 1, wallet, len(wallet)))

        # Если есть кошельки с нестандартной длиной, выводим предупреждение
        if non_standard_wallets:
            logger.warning(
                f"Обнаружены кошельки с нестандартной "
                f"длиной (стандарт: {common_length} символов):"
            )
            for line, wallet, length in non_standard_wallets:
                logger.warning(
                    f"  Строка {line}: {wallet} - {length} символов"
                )
            return False

        # Определяем тип кошельков на основе регулярных выражений
        determined_types = set()
        for wallet in self.wallets:
            wallet_type = self._determine_wallet_type(wallet)
            determined_types.add(wallet_type)

        # Если есть только один тип (кроме UNKNOWN), устанавливаем его
        if len(determined_types) == 1:
            self.wallet_type = next(iter(determined_types))
        # Если несколько типов, выбираем наиболее вероятный
        elif len(determined_types) > 1:
            # Если среди типов есть UNKNOWN, игнорируем его
            if WalletType.UNKNOWN in determined_types and len(determined_types) > 1:
                determined_types.discard(WalletType.UNKNOWN)

            # Если после удаления UNKNOWN остался один тип, используем его
            if len(determined_types) == 1:
                self.wallet_type = next(iter(determined_types))
            else:
                # Иначе подсчитываем, какой тип встречается чаще всего
                type_counts = {}
                for wallet in self.wallets:
                    wallet_type = self._determine_wallet_type(wallet)
                    if wallet_type != WalletType.UNKNOWN:
                        type_counts[wallet_type] = type_counts.get(wallet_type, 0) + 1

                if type_counts:
                    self.wallet_type = max(type_counts.items(), key=lambda x: x[1])[0]

        logger.info(f"Тип кошельков: {self.wallet_type.value}")
        return True

    def _determine_wallet_type(self, wallet: str) -> WalletType:
        """
        Определяет тип кошелька на основе его формата

        Args:
            wallet: Адрес кошелька

        Returns:
            Тип кошелька из перечисления WalletType
        """
        wallet = wallet.strip()
        for wallet_type, pattern in self.WALLET_PATTERNS.items():
            if re.match(pattern, wallet):
                return wallet_type
        return WalletType.UNKNOWN

    def _check_for_private_keys(self) -> None:
        """
        Проверяет, не загрузил ли пользователь приватные ключи вместо адресов
        (только для EVM кошельков)
        """
        if self.wallet_type == WalletType.EVM:
            expected_pk_length = self.PRIVATE_KEY_LENGTHS[WalletType.EVM]

            if self.standard_length >= expected_pk_length:
                pk_like_wallets = []
                for i, wallet in enumerate(self.wallets):
                    wallet_no_prefix = wallet.strip()
                    if wallet_no_prefix.startswith('0x'):
                        wallet_no_prefix = wallet_no_prefix[2:]

                    if len(wallet_no_prefix) == expected_pk_length and all(
                            c in '0123456789abcdefABCDEF' for c in wallet_no_prefix):
                        pk_like_wallets.append((i + 1, wallet))

                if pk_like_wallets:
                    logger.warning("⚠️ ПРЕДУПРЕЖДЕНИЕ! ⚠️")
                    logger.warning(
                        "Следующие записи похожи на "
                        "приватные ключи EVM, а не на адреса кошельков:"
                    )
                    for line, wallet in pk_like_wallets:
                        logger.warning(
                            f"  Строка {line}: {wallet}"
                        )
                    logger.warning(
                        "Публичные адреса EVM кошельков "
                        "должны начинаться с '0x' и иметь "
                        "длину 42 символа."
                    )
                    logger.warning(
                        "Проверьте, не "
                        "загрузили ли вы случайно приватные ключи!"
                    )


def check_wallets(
        file_path: str
) -> Tuple[List[str], Optional[WalletType]]:
    """
    Проверяет кошельки из файла и определяет их тип

    Args:
        file_path: Путь к файлу с кошельками

    Returns:
        Кортеж (список кошельков, тип кошельков)
    """
    try:
        with open(file_path, "r") as file:
            wallets = [line.strip() for line in file.readlines() if line.strip()]

        if not wallets:
            logger.error(
                f"Файл {file_path} пуст или "
                f"содержит только пустые строки"
            )
            return [], None

        validator = WalletValidator(wallets)
        if validator.validate():
            # Возвращаем кошельки и тип, даже если тип UNKNOWN
            return wallets, validator.wallet_type
        else:
            logger.error(
                "Проверка кошельков не пройдена. "
                "Пожалуйста, исправьте указанные ошибки."
            )
            return wallets, None

    except FileNotFoundError:
        logger.error(
            f"Файл {file_path} не найден"
        )
        return [], None
    except Exception as e:
        logger.error(
            f"Ошибка при чтении файла {file_path}: {e}"
        )
        return [], None
