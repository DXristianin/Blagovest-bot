"""
Главный файл Telegram бота для LatePoint
"""

import asyncio
import logging
import sys
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from database.db import db
from services.wordpress_api import wp_api
from services.scheduler import ReminderScheduler
from handlers import commands, callbacks
from handlers.notifications import NotificationHandler

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TelegramBotService:
    """Сервис Telegram бота"""

    def __init__(self):
        # Инициализация бота
        self.bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        # Инициализация диспетчера
        self.dp = Dispatcher()

        # Регистрация роутеров
        self.dp.include_router(commands.router)
        self.dp.include_router(callbacks.router)

        # Инициализация компонентов
        self.notification_handler = NotificationHandler(self.bot)
        self.scheduler = ReminderScheduler(self.bot)

        # Web сервер для webhook
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        """Настройка маршрутов web сервера"""
        self.app.router.add_post('/webhook/notification', self.handle_webhook)
        self.app.router.add_get('/health', self.health_check)

        # Agent token API endpoints
        self.app.router.add_post('/api/agent-token', self.handle_agent_token)
        self.app.router.add_delete('/api/unbind/{telegram_id}', self.handle_unbind)

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Обработка webhook от WordPress"""
        try:
            # Проверка секретного ключа
            webhook_secret = request.headers.get('X-Webhook-Secret')

            if webhook_secret != config.WEBHOOK_SECRET:
                logger.warning("Invalid webhook secret")
                return web.json_response({'success': False, 'message': 'Invalid secret'}, status=401)

            # Получение данных
            data = await request.json()

            event_type = data.get('event_type')
            event_data = data.get('data')

            if not event_type or not event_data:
                return web.json_response({'success': False, 'message': 'Invalid data'}, status=400)

            # Обработка уведомления
            await self.notification_handler.handle_notification(event_type, event_data)

            return web.json_response({'success': True})

        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return web.json_response({'success': False, 'message': str(e)}, status=500)

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({
            'status': 'ok',
            'service': 'telegram-bot',
            'version': '1.0.0'
        })

    async def handle_agent_token(self, request: web.Request) -> web.Response:
        """Обработка нового agent token от WordPress"""
        try:
            # Проверка секретного ключа
            webhook_secret = request.headers.get('X-Webhook-Secret')
            if webhook_secret != config.WEBHOOK_SECRET:
                logger.warning("Invalid webhook secret for agent token")
                return web.json_response({'success': False, 'message': 'Invalid secret'}, status=401)

            # Получение данных
            data = await request.json()
            token = data.get('token')
            agent_id = data.get('agent_id')
            expires_at = data.get('expires_at')

            if not token or not agent_id or not expires_at:
                return web.json_response({'success': False, 'message': 'Missing required fields'}, status=400)

            # Сохранение токена в локальную БД
            from database.models import AgentToken
            from datetime import datetime
            from sqlalchemy import select

            async with db.get_session() as session:
                # Проверка существования токена
                result = await session.execute(select(AgentToken).where(AgentToken.token == token))
                existing_token = result.scalar_one_or_none()

                if existing_token:
                    logger.info(f"Token already exists: {token[:8]}...")
                    return web.json_response({'success': True, 'message': 'Token already exists'})

                # Создание нового токена
                new_token = AgentToken(
                    token=token,
                    agent_id=agent_id,
                    expires_at=datetime.fromisoformat(expires_at.replace('Z', '+00:00')),
                    status='pending'
                )
                session.add(new_token)
                await session.commit()

                logger.info(f"Agent token saved: {token[:8]}... for agent_id={agent_id}")
                return web.json_response({'success': True, 'message': 'Token saved'})

        except Exception as e:
            logger.error(f"Error handling agent token: {e}")
            return web.json_response({'success': False, 'message': str(e)}, status=500)

    async def handle_unbind(self, request: web.Request) -> web.Response:
        """Обработка отвязки Telegram аккаунта"""
        try:
            # Проверка секретного ключа
            webhook_secret = request.headers.get('X-Webhook-Secret')
            if webhook_secret != config.WEBHOOK_SECRET:
                logger.warning("Invalid webhook secret for unbind")
                return web.json_response({'success': False, 'message': 'Invalid secret'}, status=401)

            # Получение telegram_id из URL
            telegram_id = int(request.match_info['telegram_id'])

            # Удаление привязки из БД
            from database.models import AgentBinding
            from sqlalchemy import select, delete

            async with db.get_session() as session:
                # Удаление всех привязок этого telegram_id
                result = await session.execute(
                    delete(AgentBinding).where(AgentBinding.telegram_id == telegram_id)
                )
                await session.commit()

                deleted_count = result.rowcount
                logger.info(f"Unbound telegram_id={telegram_id}, deleted {deleted_count} bindings")

                return web.json_response({
                    'success': True,
                    'message': f'Deleted {deleted_count} bindings',
                    'deleted_count': deleted_count
                })

        except ValueError:
            return web.json_response({'success': False, 'message': 'Invalid telegram_id'}, status=400)
        except Exception as e:
            logger.error(f"Error handling unbind: {e}")
            return web.json_response({'success': False, 'message': str(e)}, status=500)

    async def on_startup(self):
        """Действия при запуске бота"""
        logger.info("Starting Telegram bot...")

        # Инициализация базы данных
        await db.init_db()
        logger.info("Database initialized")

        # Инициализация WordPress API сессии
        await wp_api.init_session()
        logger.info("WordPress API session initialized")

        # Запуск планировщика напоминаний
        self.scheduler.start()
        logger.info("Reminder scheduler started")

        logger.info("Telegram bot started successfully!")

    async def on_shutdown(self):
        """Действия при остановке бота"""
        logger.info("Shutting down Telegram bot...")

        # Остановка планировщика
        self.scheduler.stop()

        # Закрытие WordPress API сессии
        await wp_api.close_session()

        # Закрытие бота
        await self.bot.session.close()

        logger.info("Telegram bot stopped")

    async def start_polling(self):
        """Запуск бота в режиме polling"""
        await self.on_startup()

        try:
            logger.info("Starting polling...")
            await self.dp.start_polling(self.bot)
        finally:
            await self.on_shutdown()

    async def start_webhook_server(self):
        """Запуск бота с web сервером для webhook"""
        await self.on_startup()

        # Запуск web сервера
        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, config.HOST, config.PORT)
        await site.start()

        logger.info(f"Web server started on {config.HOST}:{config.PORT}")
        logger.info("Bot is running in webhook mode...")

        try:
            # Запуск polling для обработки команд
            await self.dp.start_polling(self.bot)
        finally:
            await runner.cleanup()
            await self.on_shutdown()


async def main():
    """Главная функция"""
    # Проверка конфигурации
    if config.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("Bot token not configured! Please set BOT_TOKEN in config.py or environment variable.")
        sys.exit(1)

    if config.WEBHOOK_SECRET == 'YOUR_WEBHOOK_SECRET_HERE':
        logger.error("Webhook secret not configured! Please set WEBHOOK_SECRET in config.py or environment variable.")
        sys.exit(1)

    # Создание и запуск сервиса
    service = TelegramBotService()

    # Запуск в режиме webhook (с web сервером)
    await service.start_webhook_server()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
