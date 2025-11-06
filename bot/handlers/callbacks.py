"""
Обработчики callback запросов (inline кнопок)
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import db
from services.wordpress_api import wp_api
from utils.formatters import format_datetime_with_timezone
from utils.timezones import TIMEZONES, get_timezone_short_name
import config

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data.startswith('setting_toggle_'))
async def callback_toggle_setting(callback: CallbackQuery):
    """Переключение настройки уведомлений"""
    setting_name = callback.data.replace('setting_toggle_', '')

    # Получение текущих настроек
    settings = await db.get_settings(callback.message.chat.id)

    if not settings:
        await callback.answer("Настройки не найдены", show_alert=True)
        return

    # Переключение настройки
    setting_map = {
        'create': 'notify_on_create',
        'update': 'notify_on_update',
        'cancel': 'notify_on_cancel',
        'reminders': 'notify_reminders'
    }

    db_field = setting_map.get(setting_name)
    if not db_field:
        await callback.answer("Неверная настройка", show_alert=True)
        return

    # Инвертирование значения
    current_value = getattr(settings, db_field)
    new_value = not current_value

    # Обновление в БД
    await db.update_settings(callback.message.chat.id, **{db_field: new_value})

    # Обновление клавиатуры
    user = await db.get_user_by_chat_id(callback.message.chat.id)
    settings = await db.get_settings(callback.message.chat.id)
    builder = create_settings_keyboard(settings, user)

    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    await callback.answer("✅ Настройка обновлена")


@router.callback_query(F.data == 'setting_reminder_time')
async def callback_reminder_time(callback: CallbackQuery):
    """Изменение времени напоминаний"""
    settings = await db.get_settings(callback.message.chat.id)

    if not settings:
        await callback.answer("Настройки не найдены", show_alert=True)
        return

    # Клавиатура для выбора времени
    builder = InlineKeyboardBuilder()
    times = [15, 30, 60, 120, 180]

    for time_minutes in times:
        text = f"{'✅ ' if settings.reminder_minutes_before == time_minutes else ''}"

        if time_minutes < 60:
            text += f"{time_minutes} мин"
        else:
            hours = time_minutes // 60
            text += f"{hours} час{'а' if hours == 2 else ''}"

        builder.button(
            text=text,
            callback_data=f"set_reminder_{time_minutes}"
        )

    builder.button(text="« Назад", callback_data="back_to_settings")
    builder.adjust(1)

    message_text = "⏰ <b>Выберите за сколько минут до начала урока присылать напоминание:</b>"

    await callback.message.edit_text(message_text, reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('set_reminder_'))
async def callback_set_reminder_time(callback: CallbackQuery):
    """Установка времени напоминания"""
    minutes = int(callback.data.replace('set_reminder_', ''))

    # Обновление настроек
    await db.update_settings(callback.message.chat.id, reminder_minutes_before=minutes)

    # Возврат к настройкам
    user = await db.get_user_by_chat_id(callback.message.chat.id)
    settings = await db.get_settings(callback.message.chat.id)
    builder = create_settings_keyboard(settings, user)

    message_text = """⚙️ <b>Настройки уведомлений</b>

Выберите типы уведомлений, которые хотите получать:"""

    await callback.message.edit_text(message_text, reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer("✅ Время напоминания обновлено")


@router.callback_query(F.data == 'back_to_settings')
async def callback_back_to_settings(callback: CallbackQuery):
    """Возврат к настройкам"""
    user = await db.get_user_by_chat_id(callback.message.chat.id)
    settings = await db.get_settings(callback.message.chat.id)
    builder = create_settings_keyboard(settings, user)

    message_text = """⚙️ <b>Настройки уведомлений</b>

Выберите типы уведомлений, которые хотите получать:"""

    await callback.message.edit_text(message_text, reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data == 'setting_timezone')
async def callback_timezone(callback: CallbackQuery):
    """Выбор часового пояса - показать регионы"""
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки для каждого региона
    for region_key, region_data in TIMEZONES.items():
        builder.button(
            text=region_data['name'],
            callback_data=f"timezone_region_{region_key}"
        )

    builder.button(text="« Назад", callback_data="back_to_settings")
    builder.adjust(1)

    message_text = "🌍 <b>Выберите регион:</b>"

    await callback.message.edit_text(message_text, reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('timezone_region_'))
async def callback_timezone_region(callback: CallbackQuery):
    """Показать города в выбранном регионе"""
    region_key = callback.data.replace('timezone_region_', '')

    if region_key not in TIMEZONES:
        await callback.answer("Регион не найден", show_alert=True)
        return

    region_data = TIMEZONES[region_key]
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки для каждого часового пояса в регионе
    for tz_key, tz_name in region_data['zones'].items():
        builder.button(
            text=tz_name,
            callback_data=f"set_timezone_{tz_key}"
        )

    builder.button(text="« Назад к регионам", callback_data="setting_timezone")
    builder.adjust(1)

    message_text = f"🌍 <b>{region_data['name']}</b>\n\nВыберите часовой пояс:"

    await callback.message.edit_text(message_text, reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('set_timezone_'))
async def callback_set_timezone(callback: CallbackQuery):
    """Установить выбранный часовой пояс"""
    timezone = callback.data.replace('set_timezone_', '')

    # Обновление часового пояса пользователя (обрабатывает и users, и agent_bindings)
    await db.update_user_timezone(callback.message.chat.id, timezone)

    timezone_name = get_timezone_short_name(timezone)

    # Проверяем, есть ли у пользователя настройки (значит это полноценный пользователь)
    settings = await db.get_settings(callback.message.chat.id)

    if settings:
        # Это полноценный пользователь - возврат к настройкам
        user = await db.get_user_by_chat_id(callback.message.chat.id)
        builder = create_settings_keyboard(settings, user)

        message_text = """⚙️ <b>Настройки уведомлений</b>

Выберите типы уведомлений, которые хотите получать:"""

        await callback.message.edit_text(message_text, reply_markup=builder.as_markup(), parse_mode='HTML')
        await callback.answer(f"✅ Часовой пояс изменён на {timezone_name}")
    else:
        # Это пользователь привязанный только через agent_binding
        await callback.message.edit_text(
            f"✅ <b>Часовой пояс установлен!</b>\n\n"
            f"Ваш часовой пояс: {timezone_name}\n\n"
            f"Теперь все уведомления будут отображаться в вашем местном времени.",
            parse_mode='HTML'
        )
        await callback.answer(f"✅ Часовой пояс установлен: {timezone_name}")


@router.callback_query(F.data.startswith('booking_'))
async def callback_booking_action(callback: CallbackQuery):
    """Обработка действий с бронированием"""
    parts = callback.data.split('_')
    action = parts[1]  # 'details', 'approve', 'cancel', etc.
    booking_id = int(parts[2])

    user = await db.get_user_by_chat_id(callback.message.chat.id)

    if not user:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return

    if action == 'details':
        # Показать детали бронирования
        result = await wp_api.get_booking(booking_id, callback.message.chat.id)

        if not result.get('success'):
            await callback.answer("Не удалось получить детали", show_alert=True)
            return

        booking = result['booking']
        # Получение timezone пользователя
        user_timezone = user.timezone if user else None
        details_text = format_booking_details(booking, user.user_type, user_timezone)

        await callback.answer()
        await callback.message.answer(details_text, parse_mode='HTML')

    elif action == 'approve':
        # Подтвердить бронирование (только для агента)
        if user.user_type != 'agent':
            await callback.answer("Только учителя могут подтверждать бронирования", show_alert=True)
            return

        result = await wp_api.update_booking_status(booking_id, callback.message.chat.id, 'approved')

        if result.get('success'):
            await callback.answer("✅ Бронирование подтверждено")
            # Обновить сообщение
            await callback.message.edit_text(
                callback.message.text + "\n\n✅ <b>Подтверждено</b>",
                parse_mode='HTML'
            )
        else:
            await callback.answer("❌ Не удалось подтвердить бронирование", show_alert=True)

    elif action == 'cancel':
        # Отменить бронирование
        result = await wp_api.update_booking_status(booking_id, callback.message.chat.id, 'cancelled')

        if result.get('success'):
            await callback.answer("✅ Бронирование отменено")
            # Обновить сообщение
            await callback.message.edit_text(
                callback.message.text + "\n\n❌ <b>Отменено</b>",
                parse_mode='HTML'
            )
        else:
            await callback.answer("❌ Не удалось отменить бронирование", show_alert=True)


def create_settings_keyboard(settings, user=None, user_timezone=None):
    """Создание клавиатуры настроек"""
    builder = InlineKeyboardBuilder()

    # Уведомления о новых бронированиях
    create_status = "✅" if settings.notify_on_create else "❌"
    builder.button(
        text=f"{create_status} Новые бронирования",
        callback_data="setting_toggle_create"
    )

    # Уведомления об изменениях
    update_status = "✅" if settings.notify_on_update else "❌"
    builder.button(
        text=f"{update_status} Изменения",
        callback_data="setting_toggle_update"
    )

    # Уведомления об отменах
    cancel_status = "✅" if settings.notify_on_cancel else "❌"
    builder.button(
        text=f"{cancel_status} Отмены",
        callback_data="setting_toggle_cancel"
    )

    # Напоминания
    reminder_status = "✅" if settings.notify_reminders else "❌"
    builder.button(
        text=f"{reminder_status} Напоминания",
        callback_data="setting_toggle_reminders"
    )

    # Время напоминаний
    builder.button(
        text=f"⏰ За {settings.reminder_minutes_before} мин до начала",
        callback_data="setting_reminder_time"
    )

    # Часовой пояс
    if not user_timezone:
        user_timezone = user.timezone if user and user.timezone else config.TIMEZONE
    timezone_name = get_timezone_short_name(user_timezone)
    builder.button(
        text=f"🌍 Часовой пояс: {timezone_name}",
        callback_data="setting_timezone"
    )

    builder.adjust(1)
    return builder


def format_booking_details(booking: dict, user_type: str, user_timezone: str = None) -> str:
    """Форматирование деталей бронирования"""
    # Конвертация времени в часовой пояс пользователя
    start_date = booking['start_date']
    start_time = booking['start_time']
    end_time = booking['end_time']

    if user_timezone:
        start_date, start_time = format_datetime_with_timezone(
            booking['start_date'], booking['start_time'], user_timezone
        )
        _, end_time = format_datetime_with_timezone(
            booking['start_date'], booking['end_time'], user_timezone
        )

    if user_type == 'agent':
        customer = booking['customer']
        text = f"""📋 <b>Детали бронирования</b>

🆔 Код: {booking['booking_code']}
📊 Статус: {booking['status']}

👤 <b>Ученик:</b>
Имя: {customer['name']}
📧 Email: {customer['email']}
📱 Телефон: {customer['phone']}

🎵 <b>Урок:</b>
Инструмент: {booking['service']['name']}
📅 Дата: {start_date}
🕐 Время: {start_time} - {end_time}
⏱ Длительность: {booking['duration']} мин
"""
    else:
        agent = booking['agent']
        text = f"""📋 <b>Детали бронирования</b>

🆔 Код: {booking['booking_code']}
📊 Статус: {booking['status']}

👨‍🏫 <b>Учитель:</b>
Имя: {agent['name']}
📧 Email: {agent['email']}
📱 Телефон: {agent['phone']}

🎵 <b>Урок:</b>
Инструмент: {booking['service']['name']}
📅 Дата: {start_date}
🕐 Время: {start_time} - {end_time}
⏱ Длительность: {booking['duration']} мин
"""

    if booking.get('google_meet_url'):
        text += f"\n🎥 Google Meet:\n{booking['google_meet_url']}"

    return text
