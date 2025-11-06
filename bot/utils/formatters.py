"""
Утилиты для форматирования сообщений бота
"""

from datetime import datetime
import pytz
import config


def format_booking_for_agent(booking: dict) -> str:
    """
    Форматирование бронирования для учителя (подробно)

    Args:
        booking: Словарь с данными бронирования

    Returns:
        Отформатированное сообщение
    """
    customer = booking['customer']
    service = booking['service']

    text = f"""🕐 <b>{booking['start_time']} - {booking['end_time']}</b>
👤 Ученик: {customer['name']}
🎵 Инструмент: {service['name']}
📧 Email: {customer['email']}
📱 Телефон: {customer['phone']}"""

    if booking.get('google_meet_url'):
        text += f"\n🎥 Google Meet: {booking['google_meet_url']}"

    return text


def format_booking_for_customer(booking: dict) -> str:
    """
    Форматирование бронирования для ученика (подробно)

    Args:
        booking: Словарь с данными бронирования

    Returns:
        Отформатированное сообщение
    """
    agent = booking['agent']
    service = booking['service']

    text = f"""🕐 <b>{booking['start_time']} - {booking['end_time']}</b>
👨‍🏫 Учитель: {agent['name']}
🎵 Инструмент: {service['name']}"""

    if booking.get('google_meet_url'):
        text += f"\n🎥 Google Meet: {booking['google_meet_url']}"

    return text


def format_booking_for_agent_short(booking: dict) -> str:
    """
    Форматирование бронирования для учителя (кратко)

    Args:
        booking: Словарь с данными бронирования

    Returns:
        Отформатированное сообщение
    """
    customer = booking['customer']
    return f"  • {booking['start_time']} - {customer['name']} ({booking['service']['name']})"


def format_booking_for_customer_short(booking: dict) -> str:
    """
    Форматирование бронирования для ученика (кратко)

    Args:
        booking: Словарь с данными бронирования

    Returns:
        Отформатированное сообщение
    """
    agent = booking['agent']
    return f"  • {booking['start_time']} - {agent['name']} ({booking['service']['name']})"


def convert_datetime_to_timezone(date_str: str, time_str: str, target_timezone: str = None,
                                 source_timezone: str = None) -> tuple:
    """
    Конвертирует дату и время в указанный часовой пояс

    Args:
        date_str: Дата в формате YYYY-MM-DD
        time_str: Время в формате HH:MM
        target_timezone: Целевой часовой пояс (например, 'America/New_York', 'Europe/Moscow')
        source_timezone: Исходный часовой пояс (по умолчанию из config.TIMEZONE)

    Returns:
        tuple: (formatted_date, formatted_time, timezone_abbr)
    """
    # Если целевой часовой пояс не указан, используем дефолтный
    if not target_timezone:
        target_timezone = config.TIMEZONE

    # Если исходный часовой пояс не указан, используем дефолтный из конфига
    if not source_timezone:
        source_timezone = config.TIMEZONE

    try:
        # Создаем naive datetime из строк
        naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

        # Локализуем в исходном часовом поясе
        source_tz = pytz.timezone(source_timezone)
        aware_dt = source_tz.localize(naive_dt)

        # Конвертируем в целевой часовой пояс
        target_tz = pytz.timezone(target_timezone)
        converted_dt = aware_dt.astimezone(target_tz)

        # Форматируем результат
        formatted_date = converted_dt.strftime("%Y-%m-%d")
        formatted_time = converted_dt.strftime("%H:%M")
        timezone_abbr = converted_dt.strftime("%Z")

        return formatted_date, formatted_time, timezone_abbr
    except Exception as e:
        # В случае ошибки возвращаем исходные значения
        return date_str, time_str, ""


def format_datetime_with_timezone(date_str: str, time_str: str, user_timezone: str = None) -> str:
    """
    Форматирует дату и время с учетом часового пояса пользователя

    Args:
        date_str: Дата в формате YYYY-MM-DD
        time_str: Время в формате HH:MM
        user_timezone: Часовой пояс пользователя

    Returns:
        str: Отформатированная строка даты и времени
    """
    if not user_timezone or user_timezone == config.TIMEZONE:
        # Если часовой пояс не указан или совпадает с дефолтным, просто возвращаем исходные значения
        return date_str, time_str

    # Конвертируем в часовой пояс пользователя
    converted_date, converted_time, tz_abbr = convert_datetime_to_timezone(
        date_str, time_str, user_timezone
    )

    return converted_date, converted_time
