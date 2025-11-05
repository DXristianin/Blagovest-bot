"""
Планировщик для отправки напоминаний о предстоящих уроках
"""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pytz
from aiogram import Bot

import config
from database.db import db
from services.wordpress_api import wp_api

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Планировщик напоминаний"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone(config.TIMEZONE))

    def start(self):
        """Запуск планировщика"""
        # Проверка напоминаний каждые N минут
        self.scheduler.add_job(
            self.check_reminders,
            trigger=IntervalTrigger(minutes=config.REMINDER_CHECK_INTERVAL),
            id='check_reminders',
            name='Check upcoming bookings for reminders',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info(f"Reminder scheduler started (check interval: {config.REMINDER_CHECK_INTERVAL} min)")

    def stop(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()
        logger.info("Reminder scheduler stopped")

    async def check_reminders(self):
        """Проверка предстоящих уроков и отправка напоминаний"""
        logger.info("Checking for upcoming bookings...")

        try:
            # Получить всех пользователей
            users = await db.get_all_users()

            for user in users:
                # Проверить настройки
                settings = await db.get_settings(user.chat_id)

                if not settings or not settings.notify_reminders:
                    continue

                # Получить расписание на сегодня и завтра
                schedule_result = await wp_api.get_schedule(user.chat_id, period='today')

                if not schedule_result.get('success'):
                    continue

                bookings = schedule_result.get('bookings', [])

                # Проверить каждое бронирование
                for booking in bookings:
                    await self.check_and_send_reminder(user, booking, settings.reminder_minutes_before)

        except Exception as e:
            logger.error(f"Error checking reminders: {e}")

    async def check_and_send_reminder(self, user, booking: dict, minutes_before: int):
        """
        Проверить и отправить напоминание о конкретном бронировании

        Args:
            user: Пользователь из БД
            booking: Данные бронирования
            minutes_before: За сколько минут до начала отправлять напоминание
        """
        try:
            # Проверить, было ли уже отправлено напоминание
            booking_id = booking['id']
            already_sent = await db.check_reminder_sent(booking_id, user.chat_id)

            if already_sent:
                return

            # Парсинг времени начала
            start_date = booking['start_date']
            start_time = booking['start_time']

            # Формирование datetime
            start_datetime_str = f"{start_date} {start_time}"
            start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")

            # Текущее время
            now = datetime.now()

            # Время когда нужно отправить напоминание
            reminder_time = start_datetime - timedelta(minutes=minutes_before)

            # Если время напоминания прошло, но урок еще не начался
            if reminder_time <= now < start_datetime:
                # Отправить напоминание
                await self.send_reminder(user, booking)

                # Отметить как отправленное
                await db.mark_reminder_sent(booking_id, user.chat_id)

        except Exception as e:
            logger.error(f"Error processing reminder for booking {booking.get('id')}: {e}")

    async def send_reminder(self, user, booking: dict):
        """
        Отправить напоминание пользователю

        Args:
            user: Пользователь из БД
            booking: Данные бронирования
        """
        try:
            # Формирование сообщения в зависимости от типа пользователя
            if user.user_type == 'agent':
                message = self.format_reminder_for_agent(booking)
            else:
                message = self.format_reminder_for_customer(booking)

            # Отправка сообщения
            await self.bot.send_message(user.chat_id, message, parse_mode='HTML')

            # Логирование
            await db.log_notification(
                chat_id=user.chat_id,
                notification_type='reminder',
                booking_id=booking['id'],
                success=True
            )

            logger.info(f"Reminder sent to {user.name} (chat_id={user.chat_id}) for booking #{booking['id']}")

        except Exception as e:
            logger.error(f"Error sending reminder: {e}")
            await db.log_notification(
                chat_id=user.chat_id,
                notification_type='reminder',
                booking_id=booking['id'],
                success=False,
                error_message=str(e)
            )

    def format_reminder_for_agent(self, booking: dict) -> str:
        """Форматирование напоминания для учителя"""
        customer = booking['customer']
        service = booking['service']

        message = f"""⏰ <b>Напоминание о предстоящем уроке!</b>

👤 Ученик: {customer['name']}
🎵 Инструмент: {service['name']}

📅 Дата: {booking['start_date']}
🕐 Время: {booking['start_time']} - {booking['end_time']}

📧 Email: {customer['email']}
📱 Телефон: {customer['phone']}
"""

        if booking.get('google_meet_url'):
            message += f"\n🎥 Ссылка на урок:\n{booking['google_meet_url']}"

        return message

    def format_reminder_for_customer(self, booking: dict) -> str:
        """Форматирование напоминания для ученика"""
        agent = booking['agent']
        service = booking['service']

        message = f"""⏰ <b>Напоминание о предстоящем уроке!</b>

👨‍🏫 Учитель: {agent['name']}
🎵 Инструмент: {service['name']}

📅 Дата: {booking['start_date']}
🕐 Время: {booking['start_time']} - {booking['end_time']}
"""

        if booking.get('google_meet_url'):
            message += f"\n🎥 Ссылка на урок:\n{booking['google_meet_url']}\n\nЖелаем хорошего урока!"

        return message
