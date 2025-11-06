#!/usr/bin/env python3
"""
Database migration script to add timezone support
"""
import sqlite3
import sys
from pathlib import Path

def migrate():
    """Add timezone columns to users and agent_bindings tables"""
    # Определить путь к БД
    db_path = Path(__file__).parent.parent / 'bot_data.db'

    # Если БД не существует, ничего не делать
    if not db_path.exists():
        print(f'ℹ️  Database not found at {db_path}, skipping migration')
        return 0

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print('🔄 Начинаем миграцию базы данных...')

    try:
        # Проверяем таблицу users
        print('📋 Проверяем таблицу users...')
        cursor.execute('PRAGMA table_info(users)')
        columns = [col[1] for col in cursor.fetchall()]

        if 'timezone' not in columns:
            print('  ✅ Добавляем поле timezone в таблицу users...')
            cursor.execute("ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT 'Europe/Moscow'")
        else:
            print('  ℹ️  Поле timezone уже существует в таблице users')

        # Проверяем таблицу agent_bindings
        print('📋 Проверяем таблицу agent_bindings...')
        cursor.execute('PRAGMA table_info(agent_bindings)')
        columns = [col[1] for col in cursor.fetchall()]

        if 'timezone' not in columns:
            print('  ✅ Добавляем поле timezone в таблицу agent_bindings...')
            cursor.execute("ALTER TABLE agent_bindings ADD COLUMN timezone VARCHAR(50) DEFAULT 'Europe/Moscow'")
        else:
            print('  ℹ️  Поле timezone уже существует в таблице agent_bindings')

        conn.commit()
        print('✅ Миграция завершена успешно!')
        return 0

    except Exception as e:
        conn.rollback()
        print(f'❌ Ошибка миграции: {e}')
        return 1

    finally:
        conn.close()


if __name__ == '__main__':
    try:
        sys.exit(migrate())
    except Exception as e:
        print(f'❌ Критическая ошибка: {e}')
        sys.exit(1)
