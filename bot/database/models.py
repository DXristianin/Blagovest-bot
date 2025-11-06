"""
Модели базы данных для бота
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """Зарегистрированные пользователи бота"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    user_type = Column(String(20), nullable=False)  # 'agent' or 'customer'
    wp_user_id = Column(Integer, nullable=False)
    latepoint_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    timezone = Column(String(50), nullable=True, default='Europe/Moscow')  # Часовой пояс пользователя
    registered_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User(chat_id={self.chat_id}, name='{self.name}', type='{self.user_type}')>"


class Settings(Base):
    """Настройки уведомлений пользователей"""
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, unique=True, nullable=False, index=True)
    notify_on_create = Column(Boolean, default=True)
    notify_on_update = Column(Boolean, default=True)
    notify_on_cancel = Column(Boolean, default=True)
    notify_reminders = Column(Boolean, default=True)
    reminder_minutes_before = Column(Integer, default=60)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Settings(chat_id={self.chat_id})>"


class SentReminder(Base):
    """Отправленные напоминания (чтобы не дублировать)"""
    __tablename__ = 'sent_reminders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, nullable=False, index=True)
    chat_id = Column(BigInteger, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SentReminder(booking_id={self.booking_id}, chat_id={self.chat_id})>"


class NotificationLog(Base):
    """Лог отправленных уведомлений"""
    __tablename__ = 'notification_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    notification_type = Column(String(50), nullable=False)
    booking_id = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<NotificationLog(chat_id={self.chat_id}, type='{self.notification_type}')>"


class AgentToken(Base):
    """Токены для привязки агентов к Telegram аккаунтам"""
    __tablename__ = 'agent_tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    agent_id = Column(Integer, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String(20), default='pending')  # 'pending', 'used', 'expired'
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AgentToken(token={self.token[:8]}..., agent_id={self.agent_id}, status='{self.status}')>"


class AgentBinding(Base):
    """Привязки Telegram аккаунтов к агентам LatePoint"""
    __tablename__ = 'agent_bindings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, nullable=False, index=True)
    agent_id = Column(Integer, nullable=False, index=True)
    telegram_username = Column(String(255), nullable=True)
    telegram_first_name = Column(String(255), nullable=True)
    telegram_last_name = Column(String(255), nullable=True)
    timezone = Column(String(50), nullable=True, default='Europe/Moscow')  # Часовой пояс пользователя
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AgentBinding(telegram_id={self.telegram_id}, agent_id={self.agent_id})>"
