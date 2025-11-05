"""
Обработчик уведомлений от WordPress
"""

import logging
import hmac
import hashlib
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config
from database.db import db

logger = logging.getLogger(__name__)


class NotificationHandler:
    """Обработчик уведомлений"""

    def __init__(self, bot: Bot):
        self.bot = bot

    def verify_signature(self, data: dict, signature: str) -> bool:
        """Проверка подписи webhook"""
        expected_signature = hmac.new(
            config.WEBHOOK_SECRET.encode(),
            str(data).encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    async def handle_notification(self, event_type: str, data: dict):
        """
        Обработка уведомления

        Args:
            event_type: Тип события (booking_created, booking_updated, etc.)
            data: Данные бронирования
        """
        logger.info(f"Handling notification: {event_type}")

        try:
            if event_type == 'booking_created':
                await self.handle_booking_created(data)
            elif event_type == 'booking_updated':
                await self.handle_booking_updated(data)
            elif event_type == 'booking_status_changed':
                await self.handle_booking_status_changed(data)
            else:
                logger.warning(f"Unknown event type: {event_type}")

        except Exception as e:
            logger.error(f"Error handling notification: {e}")

    async def handle_booking_created(self, data: dict):
        """Обработка создания бронирования"""
        # Валидация обязательных полей
        required_fields = ['booking_id', 'agent', 'customer', 'service']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            logger.error(f"Missing required fields in booking_created: {missing_fields}")
            return

        # Дополнительная валидация вложенных полей
        if not isinstance(data.get('agent'), dict) or not isinstance(data.get('customer'), dict):
            logger.error("Invalid data structure: agent and customer must be dictionaries")
            return

        sent_telegram_ids = set()

        # Отправка уведомлений всем привязанным Telegram аккаунтам агента
        agent_id = data.get('agent_id')
        if agent_id:
            sent_telegram_ids = await self.send_to_agent_bindings(
                agent_id=agent_id,
                notification_type='booking_created',
                booking_id=data['booking_id'],
                message_formatter=lambda: self.format_booking_created_for_agent(data),
                keyboard_creator=lambda: self.create_booking_keyboard(data['booking_id'], user_type='agent')
            )

        # Fallback: старая система с telegram_chat_id (только если еще не отправили)
        agent_chat_id = data['agent'].get('telegram_chat_id')
        if agent_chat_id and int(agent_chat_id) not in sent_telegram_ids:
            # Проверка настроек
            settings = await db.get_settings(int(agent_chat_id))
            if settings and settings.notify_on_create:
                message = self.format_booking_created_for_agent(data)
                keyboard = self.create_booking_keyboard(data['booking_id'], user_type='agent')

                try:
                    await self.bot.send_message(
                        int(agent_chat_id),
                        message,
                        parse_mode='HTML',
                        reply_markup=keyboard.as_markup() if keyboard else None
                    )

                    await db.log_notification(
                        chat_id=int(agent_chat_id),
                        notification_type='booking_created',
                        booking_id=data['booking_id'],
                        success=True
                    )
                except Exception as e:
                    logger.error(f"Error sending notification to agent: {e}")
                    await db.log_notification(
                        chat_id=int(agent_chat_id),
                        notification_type='booking_created',
                        booking_id=data['booking_id'],
                        success=False,
                        error_message=str(e)
                    )

        # Отправка уведомления клиенту
        customer_chat_id = data['customer'].get('telegram_chat_id')
        if customer_chat_id:
            # Проверка настроек
            settings = await db.get_settings(int(customer_chat_id))
            if settings and settings.notify_on_create:
                message = self.format_booking_created_for_customer(data)
                keyboard = self.create_booking_keyboard(data['booking_id'], user_type='customer')

                try:
                    await self.bot.send_message(
                        int(customer_chat_id),
                        message,
                        parse_mode='HTML',
                        reply_markup=keyboard.as_markup() if keyboard else None
                    )

                    await db.log_notification(
                        chat_id=int(customer_chat_id),
                        notification_type='booking_created',
                        booking_id=data['booking_id'],
                        success=True
                    )
                except Exception as e:
                    logger.error(f"Error sending notification to customer: {e}")
                    await db.log_notification(
                        chat_id=int(customer_chat_id),
                        notification_type='booking_created',
                        booking_id=data['booking_id'],
                        success=False,
                        error_message=str(e)
                    )

    async def handle_booking_updated(self, data: dict):
        """Обработка обновления бронирования"""
        # Валидация обязательных полей
        required_fields = ['booking_id', 'agent', 'customer', 'service']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            logger.error(f"Missing required fields in booking_updated: {missing_fields}")
            return

        changes = data.get('changes', {})

        if not changes:
            return

        # Отправка уведомления агенту
        agent_chat_id = data['agent'].get('telegram_chat_id')
        if agent_chat_id:
            settings = await db.get_settings(int(agent_chat_id))
            if settings and settings.notify_on_update:
                message = self.format_booking_updated_for_agent(data, changes)

                try:
                    await self.bot.send_message(
                        int(agent_chat_id),
                        message,
                        parse_mode='HTML'
                    )
                    await db.log_notification(
                        chat_id=int(agent_chat_id),
                        notification_type='booking_updated',
                        booking_id=data['booking_id'],
                        success=True
                    )
                except Exception as e:
                    logger.error(f"Error sending update notification to agent: {e}")

        # Отправка уведомления клиенту
        customer_chat_id = data['customer'].get('telegram_chat_id')
        if customer_chat_id:
            settings = await db.get_settings(int(customer_chat_id))
            if settings and settings.notify_on_update:
                message = self.format_booking_updated_for_customer(data, changes)

                try:
                    await self.bot.send_message(
                        int(customer_chat_id),
                        message,
                        parse_mode='HTML'
                    )
                    await db.log_notification(
                        chat_id=int(customer_chat_id),
                        notification_type='booking_updated',
                        booking_id=data['booking_id'],
                        success=True
                    )
                except Exception as e:
                    logger.error(f"Error sending update notification to customer: {e}")

    async def handle_booking_status_changed(self, data: dict):
        """Обработка изменения статуса бронирования"""
        # Валидация обязательных полей
        required_fields = ['booking_id', 'agent', 'customer', 'service', 'old_status', 'new_status']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            logger.error(f"Missing required fields in booking_status_changed: {missing_fields}")
            return

        old_status = data.get('old_status')
        new_status = data.get('new_status')

        # Отправка уведомления агенту
        agent_chat_id = data['agent'].get('telegram_chat_id')
        if agent_chat_id:
            settings = await db.get_settings(int(agent_chat_id))

            # Проверка настроек в зависимости от статуса
            should_notify = False
            if new_status == 'cancelled' and settings and settings.notify_on_cancel:
                should_notify = True
            elif settings and settings.notify_on_update:
                should_notify = True

            if should_notify:
                message = self.format_status_changed_for_agent(data, old_status, new_status)

                try:
                    await self.bot.send_message(
                        int(agent_chat_id),
                        message,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Error sending status notification to agent: {e}")

        # Отправка уведомления клиенту
        customer_chat_id = data['customer'].get('telegram_chat_id')
        if customer_chat_id:
            settings = await db.get_settings(int(customer_chat_id))

            should_notify = False
            if new_status == 'cancelled' and settings and settings.notify_on_cancel:
                should_notify = True
            elif settings and settings.notify_on_update:
                should_notify = True

            if should_notify:
                message = self.format_status_changed_for_customer(data, old_status, new_status)

                try:
                    await self.bot.send_message(
                        int(customer_chat_id),
                        message,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Error sending status notification to customer: {e}")

    def format_booking_created_for_agent(self, data: dict) -> str:
        """Форматирование уведомления о новом бронировании для учителя"""
        customer = data['customer']
        service = data['service']

        message = f"""🎵 <b>Новый урок!</b>

👤 <b>Ученик:</b> {customer['name']}
📧 Email: {customer['email']}
📱 Телефон: {customer['phone']}

🎵 <b>Инструмент:</b> {service['name']}
📅 <b>Дата:</b> {data['start_date']}
🕐 <b>Время:</b> {data['start_time']} - {data['end_time']}
"""

        if data['customer'].get('timezone'):
            message += f"🌍 Часовой пояс ученика: {data['customer']['timezone']}\n"

        if data.get('google_meet_url'):
            message += f"\n🎥 <b>Google Meet:</b>\n{data['google_meet_url']}"

        message += f"\n\n🆔 Код бронирования: <code>{data['booking_code']}</code>"

        return message

    def format_booking_created_for_customer(self, data: dict) -> str:
        """Форматирование уведомления о новом бронировании для ученика"""
        agent = data['agent']
        service = data['service']

        message = f"""🎵 <b>Урок подтвержден!</b>

👨‍🏫 <b>Учитель:</b> {agent['name']}
🎵 <b>Инструмент:</b> {service['name']}

📅 <b>Дата:</b> {data['start_date']}
🕐 <b>Время:</b> {data['start_time']} - {data['end_time']}
"""

        if data.get('google_meet_url'):
            message += f"\n🎥 <b>Ссылка на урок:</b>\n{data['google_meet_url']}"

        message += "\n\nЖелаем хорошего урока! 🎶"

        return message

    def format_booking_updated_for_agent(self, data: dict, changes: dict) -> str:
        """Форматирование уведомления об изменении для учителя"""
        customer = data['customer']

        message = f"""📝 <b>Изменение в бронировании</b>

👤 <b>Ученик:</b> {customer['name']}
🎵 <b>Инструмент:</b> {data['service']['name']}

<b>Изменения:</b>
"""

        if 'start_date' in changes:
            message += f"📅 Дата: {changes['start_date']['old']} → {changes['start_date']['new']}\n"

        if 'start_time' in changes:
            message += f"🕐 Время начала: {changes['start_time']['old']} → {changes['start_time']['new']}\n"

        return message

    def format_booking_updated_for_customer(self, data: dict, changes: dict) -> str:
        """Форматирование уведомления об изменении для ученика"""
        agent = data['agent']

        message = f"""📝 <b>Изменение в бронировании</b>

👨‍🏫 <b>Учитель:</b> {agent['name']}
🎵 <b>Инструмент:</b> {data['service']['name']}

<b>Изменения:</b>
"""

        if 'start_date' in changes:
            message += f"📅 Дата: {changes['start_date']['old']} → {changes['start_date']['new']}\n"

        if 'start_time' in changes:
            message += f"🕐 Время начала: {changes['start_time']['old']} → {changes['start_time']['new']}\n"

        if data.get('google_meet_url'):
            message += f"\n🎥 <b>Ссылка на урок:</b>\n{data['google_meet_url']}"

        return message

    def format_status_changed_for_agent(self, data: dict, old_status: str, new_status: str) -> str:
        """Форматирование уведомления об изменении статуса для учителя"""
        customer = data['customer']

        status_emoji = {
            'approved': '✅',
            'cancelled': '❌',
            'pending': '⏳',
        }

        message = f"""{status_emoji.get(new_status, '📝')} <b>Статус бронирования изменен</b>

👤 <b>Ученик:</b> {customer['name']}
🎵 <b>Инструмент:</b> {data['service']['name']}
📅 <b>Дата:</b> {data['start_date']}
🕐 <b>Время:</b> {data['start_time']}

<b>Статус:</b> {old_status} → {new_status}
"""

        return message

    def format_status_changed_for_customer(self, data: dict, old_status: str, new_status: str) -> str:
        """Форматирование уведомления об изменении статуса для ученика"""
        agent = data['agent']

        status_emoji = {
            'approved': '✅',
            'cancelled': '❌',
            'pending': '⏳',
        }

        message = f"""{status_emoji.get(new_status, '📝')} <b>Статус бронирования изменен</b>

👨‍🏫 <b>Учитель:</b> {agent['name']}
🎵 <b>Инструмент:</b> {data['service']['name']}
📅 <b>Дата:</b> {data['start_date']}
🕐 <b>Время:</b> {data['start_time']}

<b>Статус:</b> {old_status} → {new_status}
"""

        return message

    def create_booking_keyboard(self, booking_id: int, user_type: str):
        """Создание клавиатуры для бронирования"""
        builder = InlineKeyboardBuilder()

        builder.button(text="📋 Детали", callback_data=f"booking_details_{booking_id}")

        if user_type == 'agent':
            builder.button(text="✅ Подтвердить", callback_data=f"booking_approve_{booking_id}")

        builder.button(text="❌ Отменить", callback_data=f"booking_cancel_{booking_id}")

        builder.adjust(1)
        return builder

    async def send_to_agent_bindings(self, agent_id: int, notification_type: str,
                                     booking_id: int, message_formatter, keyboard_creator=None):
        """
        Отправка уведомления всем Telegram аккаунтам, привязанным к агенту

        Args:
            agent_id: ID агента в LatePoint
            notification_type: Тип уведомления
            booking_id: ID бронирования
            message_formatter: Функция для форматирования сообщения
            keyboard_creator: Функция для создания клавиатуры (опционально)

        Returns:
            set: Множество telegram_id, которым были отправлены уведомления
        """
        from database.models import AgentBinding
        from sqlalchemy import select

        sent_telegram_ids = set()

        try:
            # Получить все привязки для данного агента
            async with db.get_session() as session:
                result = await session.execute(
                    select(AgentBinding).where(AgentBinding.agent_id == agent_id)
                )
                bindings = result.scalars().all()

            if not bindings:
                logger.info(f"No telegram bindings found for agent_id={agent_id}")
                return sent_telegram_ids

            logger.info(f"Found {len(bindings)} telegram bindings for agent_id={agent_id}")

            # Отправить уведомление каждому привязанному аккаунту
            for binding in bindings:
                telegram_id = binding.telegram_id

                try:
                    message = message_formatter()
                    keyboard = keyboard_creator() if keyboard_creator else None

                    await self.bot.send_message(
                        telegram_id,
                        message,
                        parse_mode='HTML',
                        reply_markup=keyboard.as_markup() if keyboard else None
                    )

                    await db.log_notification(
                        chat_id=telegram_id,
                        notification_type=notification_type,
                        booking_id=booking_id,
                        success=True
                    )

                    sent_telegram_ids.add(telegram_id)
                    logger.info(f"Notification sent to telegram_id={telegram_id} for agent_id={agent_id}")

                except Exception as e:
                    logger.error(f"Error sending notification to telegram_id={telegram_id}: {e}")
                    await db.log_notification(
                        chat_id=telegram_id,
                        notification_type=notification_type,
                        booking_id=booking_id,
                        success=False,
                        error_message=str(e)
                    )

        except Exception as e:
            logger.error(f"Error in send_to_agent_bindings: {e}")

        return sent_telegram_ids
