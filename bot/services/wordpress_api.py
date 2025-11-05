"""
Сервис для взаимодействия с WordPress API
"""

import logging
import aiohttp
from typing import Dict, List, Optional
import config

logger = logging.getLogger(__name__)


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
            async with self.session.post(url, json=data) as response:
                result = await response.json()

                if response.status == 200 and result.get('success'):
                    logger.info(f"User registered successfully: chat_id={chat_id}")
                    return result
                else:
                    logger.error(f"Registration failed: {result.get('message', 'Unknown error')}")
                    return {'success': False, 'message': result.get('message', 'Registration failed')}

        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return {'success': False, 'message': str(e)}

    async def get_schedule(self, chat_id: int, period: str = 'today') -> Dict:
        """
        Получить расписание пользователя

        Args:
            chat_id: Telegram chat ID
            period: 'today' или 'week'

        Returns:
            Dict с расписанием
        """
        await self.init_session()

        url = f"{self.base_url}/schedule"
        params = {
            'chat_id': str(chat_id),
            'period': period
        }

        try:
            async with self.session.get(url, params=params) as response:
                result = await response.json()

                if response.status == 200 and result.get('success'):
                    logger.info(f"Schedule fetched for chat_id={chat_id}, period={period}")
                    return result
                else:
                    logger.error(f"Failed to fetch schedule: {result.get('message', 'Unknown error')}")
                    return {'success': False, 'message': result.get('message', 'Failed to fetch schedule')}

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
            async with self.session.get(url, params=params) as response:
                result = await response.json()

                if response.status == 200 and result.get('success'):
                    logger.info(f"Booking {booking_id} fetched for chat_id={chat_id}")
                    return result
                else:
                    logger.error(f"Failed to fetch booking: {result.get('message', 'Unknown error')}")
                    return {'success': False, 'message': result.get('message', 'Failed to fetch booking')}

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
            async with self.session.post(url, json=data) as response:
                result = await response.json()

                if response.status == 200 and result.get('success'):
                    logger.info(f"Booking {booking_id} status updated to {new_status}")
                    return result
                else:
                    logger.error(f"Failed to update booking status: {result.get('message', 'Unknown error')}")
                    return {'success': False, 'message': result.get('message', 'Failed to update status')}

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
            async with self.session.get(url, params=params) as response:
                result = await response.json()

                if response.status == 200 and result.get('success'):
                    logger.info(f"User info fetched for chat_id={chat_id}")
                    return result
                else:
                    logger.error(f"Failed to fetch user info: {result.get('message', 'Unknown error')}")
                    return {'success': False, 'message': result.get('message', 'User not found')}

        except Exception as e:
            logger.error(f"Error fetching user info: {e}")
            return {'success': False, 'message': str(e)}


# Глобальный экземпляр
wp_api = WordPressAPI()
