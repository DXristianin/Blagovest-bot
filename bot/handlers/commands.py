"""
Обработчики команд бота
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config
from database.db import db
from services.wordpress_api import wp_api
from utils.formatters import format_datetime_with_timezone

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработка команды /start"""
    # Проверка наличия токена
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        # Нет токена - показываем приветствие
        # Проверяем есть ли привязка к агенту
        from database.models import AgentBinding
        from sqlalchemy import select

        async with db.get_session() as session:
            result = await session.execute(
                select(AgentBinding).where(AgentBinding.telegram_id == message.chat.id)
            )
            binding = result.scalar_one_or_none()

        if binding:
            await message.answer(
                f"👋 С возвращением!\n\n"
                f"Вы привязаны к агенту (ID: {binding.agent_id}).\n"
                "Вы будете получать уведомления о новых записях.\n\n"
                "Используйте /help для просмотра доступных команд."
            )
        else:
            # Проверяем старую систему регистрации
            user = await db.get_user_by_chat_id(message.chat.id)
            if user:
                await message.answer(
                    f"👋 С возвращением, {user.name}!\n\n"
                    "Используйте /help для просмотра доступных команд."
                )
            else:
                await message.answer(config.MESSAGES['welcome'])
        return

    # Есть токен - попробуем обработать как agent token
    token = args[1]
    chat_id = message.chat.id
    telegram_id = message.from_user.id
    username = message.from_user.username or ''
    first_name = message.from_user.first_name or ''
    last_name = message.from_user.last_name or ''

    # Сначала проверяем, это agent token?
    agent_token_result = await handle_agent_token(
        token, telegram_id, username, first_name, last_name
    )

    if agent_token_result is not None:
        # Это был agent token
        if agent_token_result.get('success'):
            await message.answer(
                f"✅ Успешная привязка!\n\n"
                f"Вы подключены к агенту: {agent_token_result['agent_name']}\n\n"
                "Теперь вы будете получать уведомления о новых записях к этому преподавателю."
            )
        elif 'expired' in agent_token_result.get('message', '').lower():
            await message.answer(
                "❌ Токен истёк.\n\n"
                "Пожалуйста, запросите новую ссылку у администратора."
            )
        elif 'already used' in agent_token_result.get('message', '').lower():
            await message.answer(
                "❌ Этот токен уже был использован.\n\n"
                "Пожалуйста, запросите новую ссылку у администратора."
            )
        else:
            await message.answer(
                "❌ Неверный токен.\n\n"
                "Пожалуйста, проверьте ссылку и попробуйте снова."
            )
        return

    # Если не agent token, то это старая система регистрации
    # Проверка, не зарегистрирован ли уже
    existing_user = await db.get_user_by_chat_id(chat_id)
    if existing_user:
        await message.answer(
            f"✅ Вы уже зарегистрированы как {existing_user.name}.\n\n"
            "Используйте /help для просмотра доступных команд."
        )
        return

    # Регистрация через WordPress API (старая система)
    result = await wp_api.register_user(token, chat_id, username)

    if result.get('success'):
        # Создание пользователя в локальной БД
        user_data = result
        await db.create_user(
            chat_id=chat_id,
            username=username,
            user_type=user_data['user_type'],
            wp_user_id=user_data['user_id'],
            latepoint_id=user_data.get('user_id', 0),  # Используем wp_user_id как fallback
            name=user_data['name'],
            email=user_data['email']
        )

        # Определение типа пользователя для сообщения
        user_type_text = 'Учитель' if user_data['user_type'] == 'agent' else 'Ученик'

        message_text = config.MESSAGES['registration_success'].format(
            name=user_data['name'],
            user_type=user_type_text
        )
        await message.answer(message_text)

    elif 'expired' in result.get('message', '').lower():
        await message.answer(config.MESSAGES['token_expired'])
    else:
        await message.answer(config.MESSAGES['invalid_token'])


async def handle_agent_token(token: str, telegram_id: int, username: str,
                             first_name: str, last_name: str) -> dict:
    """
    Обработка agent token
    Возвращает None если это не agent token, или dict с результатом
    """
    from database.models import AgentToken, AgentBinding
    from sqlalchemy import select, delete
    from datetime import datetime, timezone
    import aiohttp

    try:
        # Проверяем токен в локальной БД
        async with db.get_session() as session:
            result = await session.execute(
                select(AgentToken).where(AgentToken.token == token)
            )
            agent_token = result.scalar_one_or_none()

            if not agent_token:
                # Это не agent token
                return None

            # Проверка статуса и срока действия
            if agent_token.status != 'pending':
                return {'success': False, 'message': 'Token already used or revoked'}

            if agent_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                return {'success': False, 'message': 'Token expired'}

            # Удалить старую привязку этого telegram_id (если есть)
            await session.execute(
                delete(AgentBinding).where(AgentBinding.telegram_id == telegram_id)
            )

            # Создать новую привязку
            new_binding = AgentBinding(
                telegram_id=telegram_id,
                agent_id=agent_token.agent_id,
                telegram_username=username,
                telegram_first_name=first_name,
                telegram_last_name=last_name
            )
            session.add(new_binding)

            # Пометить токен как использованный
            agent_token.status = 'used'

            await session.commit()

            agent_id = agent_token.agent_id

        # Уведомить WordPress об использовании токена
        async with aiohttp.ClientSession() as http_session:
            try:
                async with http_session.post(
                    f"{config.WP_API_URL}/agent-token/confirm",
                    json={
                        'token': token,
                        'telegram_id': telegram_id,
                        'telegram_data': {
                            'username': username,
                            'first_name': first_name,
                            'last_name': last_name
                        }
                    },
                    headers={'X-Webhook-Secret': config.WEBHOOK_SECRET},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    wp_result = await response.json()
                    logger.info(f"WordPress confirmation: {wp_result}")

                    return {
                        'success': True,
                        'agent_id': agent_id,
                        'agent_name': wp_result.get('agent_name', f'Agent {agent_id}')
                    }
            except Exception as e:
                logger.error(f"Error notifying WordPress: {e}")
                # Всё равно возвращаем успех, т.к. локально сохранили
                return {
                    'success': True,
                    'agent_id': agent_id,
                    'agent_name': f'Agent {agent_id}'
                }

    except Exception as e:
        logger.error(f"Error handling agent token: {e}")
        return {'success': False, 'message': str(e)}


@router.message(Command('help'))
async def cmd_help(message: Message):
    """Обработка команды /help"""
    await message.answer(config.MESSAGES['help'])


@router.message(Command('today'))
async def cmd_today(message: Message):
    """Обработка команды /today - уроки на сегодня"""
    user = await db.get_user_by_chat_id(message.chat.id)

    if not user:
        await message.answer(config.MESSAGES['not_registered'])
        return

    # Получение расписания
    result = await wp_api.get_schedule(message.chat.id, period='today')

    if not result.get('success'):
        await message.answer("❌ Не удалось получить расписание. Попробуйте позже.")
        return

    bookings = result.get('bookings', [])

    if not bookings:
        await message.answer("📅 На сегодня уроков нет.")
        return

    # Получение timezone пользователя
    user_timezone = user.timezone if user else None

    # Формирование сообщения
    message_text = f"📅 <b>Уроки на сегодня ({result['period']['from']}):</b>\n\n"

    for booking in bookings:
        if user.user_type == 'agent':
            message_text += format_booking_for_agent(booking, user_timezone)
        else:
            message_text += format_booking_for_customer(booking, user_timezone)
        message_text += "\n---\n\n"

    await message.answer(message_text, parse_mode='HTML')


@router.message(Command('week'))
async def cmd_week(message: Message):
    """Обработка команды /week - уроки на неделю"""
    user = await db.get_user_by_chat_id(message.chat.id)

    if not user:
        await message.answer(config.MESSAGES['not_registered'])
        return

    # Получение расписания
    result = await wp_api.get_schedule(message.chat.id, period='week')

    if not result.get('success'):
        await message.answer("❌ Не удалось получить расписание. Попробуйте позже.")
        return

    bookings = result.get('bookings', [])

    if not bookings:
        await message.answer("📅 На ближайшую неделю уроков нет.")
        return

    # Получение timezone пользователя
    user_timezone = user.timezone if user else None

    # Группировка по датам
    bookings_by_date = {}
    for booking in bookings:
        date = booking['start_date']
        if date not in bookings_by_date:
            bookings_by_date[date] = []
        bookings_by_date[date].append(booking)

    # Формирование сообщения
    message_text = f"📅 <b>Уроки на неделю ({result['period']['from']} - {result['period']['to']}):</b>\n\n"

    for date, day_bookings in sorted(bookings_by_date.items()):
        message_text += f"📆 <b>{date}</b>\n"

        for booking in day_bookings:
            if user.user_type == 'agent':
                message_text += format_booking_for_agent_short(booking, user_timezone)
            else:
                message_text += format_booking_for_customer_short(booking, user_timezone)
            message_text += "\n"

        message_text += "\n"

    await message.answer(message_text, parse_mode='HTML')


@router.message(Command('settings'))
async def cmd_settings(message: Message):
    """Обработка команды /settings - настройки уведомлений"""
    user = await db.get_user_by_chat_id(message.chat.id)

    if not user:
        await message.answer(config.MESSAGES['not_registered'])
        return

    # Получение текущих настроек
    settings = await db.get_settings(message.chat.id)

    if not settings:
        await message.answer("❌ Настройки не найдены.")
        return

    # Формирование клавиатуры с inline кнопками
    builder = InlineKeyboardBuilder()

    # Уведомления о новых бронированиях
    create_status = "✅" if settings.notify_on_create else "❌"
    builder.button(
        text=f"{create_status} Новые бронирования",
        callback_data=f"setting_toggle_create"
    )

    # Уведомления об изменениях
    update_status = "✅" if settings.notify_on_update else "❌"
    builder.button(
        text=f"{update_status} Изменения",
        callback_data=f"setting_toggle_update"
    )

    # Уведомления об отменах
    cancel_status = "✅" if settings.notify_on_cancel else "❌"
    builder.button(
        text=f"{cancel_status} Отмены",
        callback_data=f"setting_toggle_cancel"
    )

    # Напоминания
    reminder_status = "✅" if settings.notify_reminders else "❌"
    builder.button(
        text=f"{reminder_status} Напоминания",
        callback_data=f"setting_toggle_reminders"
    )

    # Время напоминаний
    builder.button(
        text=f"⏰ За {settings.reminder_minutes_before} мин до начала",
        callback_data=f"setting_reminder_time"
    )

    builder.adjust(1)  # По одной кнопке в ряд

    message_text = """⚙️ <b>Настройки уведомлений</b>

Выберите типы уведомлений, которые хотите получать:"""

    await message.answer(message_text, reply_markup=builder.as_markup(), parse_mode='HTML')


def format_booking_for_agent(booking: dict, user_timezone: str = None) -> str:
    """Форматирование бронирования для учителя (подробно)"""
    customer = booking['customer']
    service = booking['service']

    # Конвертация времени в часовой пояс пользователя
    start_time = booking['start_time']
    end_time = booking['end_time']

    if user_timezone:
        _, start_time = format_datetime_with_timezone(
            booking['start_date'], booking['start_time'], user_timezone
        )
        _, end_time = format_datetime_with_timezone(
            booking['start_date'], booking['end_time'], user_timezone
        )

    text = f"""🕐 <b>{start_time} - {end_time}</b>
👤 Ученик: {customer['name']}
🎵 Инструмент: {service['name']}
📧 Email: {customer['email']}
📱 Телефон: {customer['phone']}"""

    if booking.get('google_meet_url'):
        text += f"\n🎥 Google Meet: {booking['google_meet_url']}"

    return text


def format_booking_for_customer(booking: dict, user_timezone: str = None) -> str:
    """Форматирование бронирования для ученика (подробно)"""
    agent = booking['agent']
    service = booking['service']

    # Конвертация времени в часовой пояс пользователя
    start_time = booking['start_time']
    end_time = booking['end_time']

    if user_timezone:
        _, start_time = format_datetime_with_timezone(
            booking['start_date'], booking['start_time'], user_timezone
        )
        _, end_time = format_datetime_with_timezone(
            booking['start_date'], booking['end_time'], user_timezone
        )

    text = f"""🕐 <b>{start_time} - {end_time}</b>
👨‍🏫 Учитель: {agent['name']}
🎵 Инструмент: {service['name']}"""

    if booking.get('google_meet_url'):
        text += f"\n🎥 Google Meet: {booking['google_meet_url']}"

    return text


def format_booking_for_agent_short(booking: dict, user_timezone: str = None) -> str:
    """Форматирование бронирования для учителя (кратко)"""
    customer = booking['customer']

    # Конвертация времени в часовой пояс пользователя
    start_time = booking['start_time']

    if user_timezone:
        _, start_time = format_datetime_with_timezone(
            booking['start_date'], booking['start_time'], user_timezone
        )

    return f"  • {start_time} - {customer['name']} ({booking['service']['name']})"


def format_booking_for_customer_short(booking: dict, user_timezone: str = None) -> str:
    """Форматирование бронирования для ученика (кратко)"""
    agent = booking['agent']

    # Конвертация времени в часовой пояс пользователя
    start_time = booking['start_time']

    if user_timezone:
        _, start_time = format_datetime_with_timezone(
            booking['start_date'], booking['start_time'], user_timezone
        )

    return f"  • {start_time} - {agent['name']} ({booking['service']['name']})"
