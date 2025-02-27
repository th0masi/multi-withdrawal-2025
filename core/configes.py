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

            config_path = os.path.join(project_root_path, "data", "config.toml")

            if not os.path.exists(config_path):
                alt_config_path = os.path.join(project_root_path, "data/config.toml")
                if os.path.exists(alt_config_path):
                    config_path = alt_config_path
                else:
                    root_config_path = os.path.join(project_root_path, "config.toml")
                    if os.path.exists(root_config_path):
                        config_path = root_config_path
                    else:
                        raise FileNotFoundError(
                            f"Файл конфигурации не найден по пути: {config_path}"
                        )

            with open(config_path, "rb") as config_file:
                return msgspec.toml.decode(config_file.read(), type=cls)

        except FileNotFoundError:
            logger.error(f"Файл конфигурации config.toml не найден: {config_path}")
            raise
        except PermissionError:
            logger.error(f"Нет доступа к файлу конфигурации config.toml")
            raise
        except Exception as e:
            logger.error(f"Ошибка при загрузке конфигурации: {str(e)}")
            raise
