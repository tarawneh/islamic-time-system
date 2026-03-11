from __future__ import annotations
from pathlib import Path
from typing import Iterable
import mysql.connector
from mysql_config import load_mysql_config

def get_connection(database_required: bool = True):
    cfg = load_mysql_config()
    kwargs = dict(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        charset=cfg.charset,
        use_unicode=True,
        autocommit=True,
    )
    if database_required:
        kwargs["database"] = cfg.database
    return mysql.connector.connect(**kwargs)

def test_connection():
    with get_connection(database_required=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION(), @@hostname")
            version, hostname = cur.fetchone()
            return str(version), str(hostname)

def ensure_database_exists():
    cfg = load_mysql_config()
    sql = (
        f"CREATE DATABASE IF NOT EXISTS `{cfg.database}` "
        f"CHARACTER SET {cfg.charset} COLLATE {cfg.charset}_unicode_ci"
    )
    with get_connection(database_required=False) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)

def execute_sql_script(sql_path: str | Path):
    sql_text = Path(sql_path).read_text(encoding="utf-8")
    statements = _split_sql_statements(sql_text)
    with get_connection(database_required=True) as conn:
        with conn.cursor() as cur:
            for statement in statements:
                cleaned = statement.strip()
                if cleaned:
                    cur.execute(cleaned)

def _split_sql_statements(sql_text: str) -> Iterable[str]:
    parts = []
    current = []
    in_string = False
    string_char = ""
    prev = ""
    for ch in sql_text:
        if ch in ("'", '"') and prev != "\\":
            if not in_string:
                in_string = True
                string_char = ch
            elif string_char == ch:
                in_string = False
                string_char = ""
        if ch == ";" and not in_string:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
        prev = ch
    if current:
        parts.append("".join(current))
    return parts
