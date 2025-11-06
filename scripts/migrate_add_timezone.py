#!/usr/bin/env python3
"""
Миграция базы данных: добавление поля timezone в таблицы users и agent_bindings
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent / 'bot'))

from sqlalchemy import text
from database.db import db


async def migrate():
    """Выполнить миграцию базы данных"""
    print("🔄 Начинаем миграцию базы данных...")

    async with db.engine.begin() as conn:
        # Проверяем и добавляем поле timezone в таблицу users
        print("📋 Проверяем таблицу users...")

        # Проверяем существование столбца timezone в users
        result = await conn.execute(text(
            "SELECT COUNT(*) as cnt FROM pragma_table_info('users') WHERE name='timezone'"
        ))
        has_timezone_in_users = result.scalar() > 0

        if not has_timezone_in_users:
            print("  ✅ Добавляем поле timezone в таблицу users...")
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT 'Europe/Moscow'"
            ))
            print("  ✅ Поле timezone добавлено в users")
        else:
            print("  ℹ️  Поле timezone уже существует в users")

        # Проверяем и добавляем поле timezone в таблицу agent_bindings
        print("📋 Проверяем таблицу agent_bindings...")

        # Проверяем существование столбца timezone в agent_bindings
        result = await conn.execute(text(
            "SELECT COUNT(*) as cnt FROM pragma_table_info('agent_bindings') WHERE name='timezone'"
        ))
        has_timezone_in_bindings = result.scalar() > 0

        if not has_timezone_in_bindings:
            print("  ✅ Добавляем поле timezone в таблицу agent_bindings...")
            await conn.execute(text(
                "ALTER TABLE agent_bindings ADD COLUMN timezone VARCHAR(50) DEFAULT 'Europe/Moscow'"
            ))
            print("  ✅ Поле timezone добавлено в agent_bindings")
        else:
            print("  ℹ️  Поле timezone уже существует в agent_bindings")

    print("✅ Миграция завершена успешно!")


if __name__ == '__main__':
    asyncio.run(migrate())
