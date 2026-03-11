from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class MySQLConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    charset: str = "utf8mb4"

def load_mysql_config() -> MySQLConfig:
    return MySQLConfig(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        database=os.environ.get("MYSQL_DATABASE", "islamic_time_system"),
        user=os.environ.get("MYSQL_USER", ""),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        charset=os.environ.get("MYSQL_CHARSET", "utf8mb4"),
    )
