import os

import msgspec.toml
from loguru import logger
from msgspec import Struct


class Data3Type(Struct):
    api_key: str
    api_secret: str
    password: str


class Data2Type(Struct):
    api_key: str
    api_secret: str


class Settings(Struct):
    okx: Data3Type
    mexc: Data2Type
    bitget: Data3Type
    binance: Data3Type
    bybit: Data2Type
    gate: Data2Type
    kucoin: Data3Type
    htx: Data2Type
    coinex: Data2Type

class Config(Struct):
    settings: Settings

    @classmethod
    def load(cls) -> "Config":
        config_path = None
        try:
            current_file_path = os.path.abspath(__file__)
            current_dir_path = os.path.dirname(current_file_path)
            project_root_path = os.path.dirname(current_dir_path)
            config_path = os.path.join(project_root_path, "data\config.toml")

            with open(config_path, "rb") as config_file:
                return msgspec.toml.decode(config_file.read(), type=cls)

        except FileNotFoundError:
            logger.error(f"файл конфигурации config.toml не найден: {config_path}")
        except PermissionError:
            logger.error(f"нет доступа к файлу конфигурации config.toml")
        except Exception as e:
            logger.error(f"ошибка при загрузке конфигурации: {str(e)}")
