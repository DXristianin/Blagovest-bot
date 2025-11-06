"""
Константы часовых поясов для выбора пользователем
"""

# Словарь с часовыми поясами по регионам
TIMEZONES = {
    'russia': {
        'name': 'Россия 🇷🇺',
        'zones': {
            'Europe/Moscow': 'Москва (МСК, UTC+3)',
            'Europe/Kaliningrad': 'Калининград (UTC+2)',
            'Asia/Yekaterinburg': 'Екатеринбург (UTC+5)',
            'Asia/Omsk': 'Омск (UTC+6)',
            'Asia/Krasnoyarsk': 'Красноярск (UTC+7)',
            'Asia/Irkutsk': 'Иркутск (UTC+8)',
            'Asia/Yakutsk': 'Якутск (UTC+9)',
            'Asia/Vladivostok': 'Владивосток (UTC+10)',
        }
    },
    'usa': {
        'name': 'США 🇺🇸',
        'zones': {
            'America/New_York': 'Нью-Йорк / Вашингтон (EST, UTC-5)',
            'America/Chicago': 'Чикаго (CST, UTC-6)',
            'America/Denver': 'Денвер (MST, UTC-7)',
            'America/Los_Angeles': 'Лос-Анджелес (PST, UTC-8)',
            'America/Anchorage': 'Анкоридж (AKST, UTC-9)',
            'Pacific/Honolulu': 'Гонолулу (HST, UTC-10)',
        }
    },
    'europe': {
        'name': 'Европа 🇪🇺',
        'zones': {
            'Europe/London': 'Лондон (GMT, UTC+0)',
            'Europe/Paris': 'Париж (CET, UTC+1)',
            'Europe/Berlin': 'Берлин (CET, UTC+1)',
            'Europe/Rome': 'Рим (CET, UTC+1)',
            'Europe/Kiev': 'Киев (EET, UTC+2)',
            'Europe/Minsk': 'Минск (UTC+3)',
            'Europe/Athens': 'Афины (EET, UTC+2)',
            'Europe/Istanbul': 'Стамбул (TRT, UTC+3)',
        }
    },
    'asia': {
        'name': 'Азия 🌏',
        'zones': {
            'Asia/Dubai': 'Дубай (UTC+4)',
            'Asia/Tashkent': 'Ташкент (UTC+5)',
            'Asia/Almaty': 'Алматы (UTC+6)',
            'Asia/Bangkok': 'Бангкок (UTC+7)',
            'Asia/Shanghai': 'Шанхай (CST, UTC+8)',
            'Asia/Tokyo': 'Токио (JST, UTC+9)',
            'Asia/Seoul': 'Сеул (KST, UTC+9)',
            'Asia/Singapore': 'Сингапур (UTC+8)',
        }
    },
    'other': {
        'name': 'Другие 🌍',
        'zones': {
            'Australia/Sydney': 'Сидней (AEDT, UTC+11)',
            'Pacific/Auckland': 'Окленд (NZDT, UTC+13)',
            'America/Sao_Paulo': 'Сан-Паулу (BRT, UTC-3)',
            'America/Argentina/Buenos_Aires': 'Буэнос-Айрес (ART, UTC-3)',
            'Africa/Cairo': 'Каир (EET, UTC+2)',
            'Africa/Johannesburg': 'Йоханнесбург (SAST, UTC+2)',
        }
    }
}


def get_timezone_display_name(timezone: str) -> str:
    """
    Получить отображаемое имя часового пояса

    Args:
        timezone: Строка часового пояса (например, 'Europe/Moscow')

    Returns:
        Читаемое имя (например, 'Москва (МСК, UTC+3)')
    """
    for region_data in TIMEZONES.values():
        if timezone in region_data['zones']:
            return region_data['zones'][timezone]

    # Если не найден, возвращаем сам часовой пояс
    return timezone.replace('_', ' ').split('/')[-1]


def get_timezone_short_name(timezone: str) -> str:
    """
    Получить короткое имя часового пояса (только город)

    Args:
        timezone: Строка часового пояса (например, 'Europe/Moscow')

    Returns:
        Короткое имя (например, 'Москва')
    """
    full_name = get_timezone_display_name(timezone)
    # Берём часть до первой скобки
    return full_name.split('(')[0].strip()
