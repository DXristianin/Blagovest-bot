"""
Менеджер базы данных
"""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, and_
from database.models import Base, User, Settings, SentReminder, NotificationLog
import config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер для работы с базой данных"""

    def __init__(self):
        self.engine = create_async_engine(config.DATABASE_URL, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """Инициализация базы данных"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")

    async def get_user_by_chat_id(self, chat_id: int) -> User | None:
        """Получить пользователя по chat_id"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.chat_id == chat_id)
            )
            return result.scalar_one_or_none()

    async def create_user(self, chat_id: int, username: str, user_type: str,
                         wp_user_id: int, latepoint_id: int, name: str, email: str) -> User:
        """Создать нового пользователя"""
        async with self.async_session() as session:
            user = User(
                chat_id=chat_id,
                username=username,
                user_type=user_type,
                wp_user_id=wp_user_id,
                latepoint_id=latepoint_id,
                name=name,
                email=email
            )
            session.add(user)

            # Создать настройки по умолчанию
            settings = Settings(chat_id=chat_id)
            session.add(settings)

            await session.commit()
            await session.refresh(user)
            logger.info(f"User created: {user}")
            return user

    async def get_settings(self, chat_id: int) -> Settings | None:
        """Получить настройки пользователя"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Settings).where(Settings.chat_id == chat_id)
            )
            return result.scalar_one_or_none()

    async def update_settings(self, chat_id: int, **kwargs) -> Settings:
        """Обновить настройки пользователя"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Settings).where(Settings.chat_id == chat_id)
            )
            settings = result.scalar_one_or_none()

            if not settings:
                settings = Settings(chat_id=chat_id)
                session.add(settings)

            for key, value in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)

            await session.commit()
            await session.refresh(settings)
            logger.info(f"Settings updated for chat_id={chat_id}")
            return settings

    async def check_reminder_sent(self, booking_id: int, chat_id: int) -> bool:
        """Проверить, было ли отправлено напоминание"""
        async with self.async_session() as session:
            result = await session.execute(
                select(SentReminder).where(
                    and_(
                        SentReminder.booking_id == booking_id,
                        SentReminder.chat_id == chat_id
                    )
                )
            )
            return result.scalar_one_or_none() is not None

    async def mark_reminder_sent(self, booking_id: int, chat_id: int):
        """Отметить напоминание как отправленное"""
        async with self.async_session() as session:
            reminder = SentReminder(booking_id=booking_id, chat_id=chat_id)
            session.add(reminder)
            await session.commit()
            logger.info(f"Reminder marked as sent: booking_id={booking_id}, chat_id={chat_id}")

    async def log_notification(self, chat_id: int, notification_type: str,
                               booking_id: int | None, success: bool,
                               error_message: str | None = None):
        """Логировать отправленное уведомление"""
        async with self.async_session() as session:
            log = NotificationLog(
                chat_id=chat_id,
                notification_type=notification_type,
                booking_id=booking_id,
                success=success,
                error_message=error_message
            )
            session.add(log)
            await session.commit()

    async def get_all_users(self) -> list[User]:
        """Получить всех пользователей"""
        async with self.async_session() as session:
            result = await session.execute(select(User))
            return result.scalars().all()

    async def get_users_by_type(self, user_type: str) -> list[User]:
        """Получить пользователей по типу"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.user_type == user_type)
            )
            return result.scalars().all()

    def get_session(self):
        """Получить новую сессию базы данных"""
        return self.async_session()


# Глобальный экземпляр
db = DatabaseManager()
