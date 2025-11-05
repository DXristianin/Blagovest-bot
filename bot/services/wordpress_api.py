"""
Сервис для взаимодействия с WordPress API
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Optional
import config

logger = logging.getLogger(__name__)

# Константа для таймаута запросов
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=config.HTTP_TIMEOUT)


class WordPressAPI:
    """Клиент для работы с WordPress REST API"""

    def __init__(self):
        self.base_url = config.WP_API_URL
        self.session: Optional[aiohttp.ClientSession] = None

    async def init_session(self):
        """Инициализация HTTP сессии"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            logger.info("WordPress API session initialized")

    async def close_session(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()
            logger.info("WordPress API session closed")

    async def _handle_response(self, response: aiohttp.ClientResponse, operation: str) -> Dict:
        """
        Обработка HTTP ответа с проверкой статус кодов

        Args:
            response: HTTP ответ от aiohttp
            operation: Название операции для логирования

        Returns:
            Dict с результатом
        """
        try:
            # Проверка статуса
            if response.status >= 500:
                logger.error(f"{operation}: Server error {response.status}")
                return {'success': False, 'message': f'Server error: {response.status}'}

            if response.status >= 400:
                logger.warning(f"{operation}: Client error {response.status}")
                try:
                    error_data = await response.json()
                    return {'success': False, 'message': error_data.get('message', f'Client error: {response.status}')}
                except:
                    return {'success': False, 'message': f'Client error: {response.status}'}

            # Парсинг JSON
            try:
                result = await response.json()
                return result
            except aiohttp.ContentTypeError:
                logger.error(f"{operation}: Invalid JSON response")
                return {'success': False, 'message': 'Invalid JSON response'}

        except Exception as e:
            logger.error(f"{operation}: Error handling response: {e}")
            return {'success': False, 'message': str(e)}

    async def register_user(self, token: str, chat_id: int, username: str) -> Dict:
        """
        Регистрация пользователя в WordPress

        Args:
            token: Токен регистрации
            chat_id: Telegram chat ID
            username: Telegram username

        Returns:
            Dict с данными пользователя
        """
        await self.init_session()

        url = f"{self.base_url}/register"
        data = {
            'token': token,
            'chat_id': str(chat_id),
            'username': username
        }

        try:
            async with self.session.post(url, json=data, timeout=REQUEST_TIMEOUT) as response:
                result = await self._handle_response(response, "User registration")

                if result.get('success'):
                    logger.info(f"User registered successfully: chat_id={chat_id}")

                return result

        except asyncio.TimeoutError:
            logger.error(f"Timeout registering user: chat_id={chat_id}")
            return {'success': False, 'message': 'Request timeout'}
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return {'success': False, 'message': str(e)}

    async def get_schedule(self, chat_id: int, period: str = None, date_from: str = None, date_to: str = None) -> Dict:
        """
        Получить расписание пользователя

        Args:
            chat_id: Telegram chat ID
            period: 'today' или 'week' (опционально)
            date_from: Начальная дата в формате YYYY-MM-DD (опционально)
            date_to: Конечная дата в формате YYYY-MM-DD (опционально)

        Returns:
            Dict с расписанием
        """
        await self.init_session()

        url = f"{self.base_url}/schedule"
        params = {'chat_id': str(chat_id)}

        if period:
            params['period'] = period
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to

        try:
            async with self.session.get(url, params=params, timeout=REQUEST_TIMEOUT) as response:
                result = await self._handle_response(response, "Get schedule")

                if result.get('success'):
                    logger.info(f"Schedule fetched for chat_id={chat_id}")

                return result

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching schedule for chat_id={chat_id}")
            return {'success': False, 'message': 'Request timeout'}
        except Exception as e:
            logger.error(f"Error fetching schedule: {e}")
            return {'success': False, 'message': str(e)}

    async def get_booking(self, booking_id: int, chat_id: int) -> Dict:
        """
        Получить детали бронирования

        Args:
            booking_id: ID бронирования
            chat_id: Telegram chat ID

        Returns:
            Dict с деталями бронирования
        """
        await self.init_session()

        url = f"{self.base_url}/booking/{booking_id}"
        params = {'chat_id': str(chat_id)}

        try:
            async with self.session.get(url, params=params, timeout=REQUEST_TIMEOUT) as response:
                result = await self._handle_response(response, f"Get booking {booking_id}")

                if result.get('success'):
                    logger.info(f"Booking {booking_id} fetched for chat_id={chat_id}")

                return result

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching booking {booking_id}")
            return {'success': False, 'message': 'Request timeout'}
        except Exception as e:
            logger.error(f"Error fetching booking: {e}")
            return {'success': False, 'message': str(e)}

    async def update_booking_status(self, booking_id: int, chat_id: int, new_status: str) -> Dict:
        """
        Обновить статус бронирования

        Args:
            booking_id: ID бронирования
            chat_id: Telegram chat ID
            new_status: Новый статус (approved, cancelled, etc.)

        Returns:
            Dict с результатом
        """
        await self.init_session()

        url = f"{self.base_url}/booking/{booking_id}/status"
        data = {
            'chat_id': str(chat_id),
            'status': new_status
        }

        try:
            async with self.session.post(url, json=data, timeout=REQUEST_TIMEOUT) as response:
                result = await self._handle_response(response, f"Update booking {booking_id} status")

                if result.get('success'):
                    logger.info(f"Booking {booking_id} status updated to {new_status}")

                return result

        except asyncio.TimeoutError:
            logger.error(f"Timeout updating booking {booking_id} status")
            return {'success': False, 'message': 'Request timeout'}
        except Exception as e:
            logger.error(f"Error updating booking status: {e}")
            return {'success': False, 'message': str(e)}

    async def get_user_info(self, chat_id: int) -> Dict:
        """
        Получить информацию о пользователе

        Args:
            chat_id: Telegram chat ID

        Returns:
            Dict с информацией о пользователе
        """
        await self.init_session()

        url = f"{self.base_url}/user-info"
        params = {'chat_id': str(chat_id)}

        try:
            async with self.session.get(url, params=params, timeout=REQUEST_TIMEOUT) as response:
                result = await self._handle_response(response, "Get user info")

                if result.get('success'):
                    logger.info(f"User info fetched for chat_id={chat_id}")

                return result

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching user info for chat_id={chat_id}")
            return {'success': False, 'message': 'Request timeout'}
        except Exception as e:
            logger.error(f"Error fetching user info: {e}")
            return {'success': False, 'message': str(e)}


# Глобальный экземпляр
wp_api = WordPressAPI()
