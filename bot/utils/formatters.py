"""
Утилиты для форматирования сообщений бота
"""


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
