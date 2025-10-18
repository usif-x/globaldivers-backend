import logging
from typing import Optional

import requests

from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"


class TelegramBot:
    def __init__(self, token: str):
        self.token = token

    def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
    ) -> bool:
        """
        Send a message to a specific chat/user.

        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: Message formatting (HTML or Markdown)
            disable_web_page_preview: Whether to disable link previews

        Returns:
            bool: True if message was sent successfully
        """
        if not self.token:
            logger.error("Telegram bot token is not configured")
            return False

        url = TELEGRAM_API_URL.format(token=self.token, method="sendMessage")
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"Message sent successfully to chat_id: {chat_id}")
                return True
            else:
                logger.error(f"Failed to send message to {chat_id}: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message to {chat_id}: {str(e)}")
            return False

    def get_me(self) -> Optional[dict]:
        """Get bot information to test if the token is valid."""
        if not self.token:
            return None

        url = TELEGRAM_API_URL.format(token=self.token, method="getMe")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException:
            return None


# Initialize bot instance
telegram_bot = TelegramBot(token=settings.TELEGRAM_BOT_TOKEN)


def notify_admins(
    message: str, parse_mode: str = "HTML", add_timestamp: bool = True
) -> dict:
    """
    Send notification message to all configured admin users.

    Args:
        message: The message to send
        parse_mode: Message formatting (HTML or Markdown)
        add_timestamp: Whether to add timestamp to the message

    Returns:
        dict: Results of sending to each admin
    """
    if not settings.TELEGRAM_ADMIN_IDS:
        logger.warning("No Telegram admin IDs configured")
        return {"error": "No admin IDs configured"}

    if add_timestamp:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"🔔 <b>Global Divers Notification</b>\n\n{message}\n\n<i>📅 {timestamp}</i>"

    results = {}
    success_count = 0

    for admin_id in settings.TELEGRAM_ADMIN_IDS:
        try:
            success = telegram_bot.send_message(
                chat_id=admin_id, text=message, parse_mode=parse_mode
            )
            results[admin_id] = "success" if success else "failed"
            if success:
                success_count += 1
        except Exception as e:
            logger.error(f"Error notifying admin {admin_id}: {str(e)}")
            results[admin_id] = f"error: {str(e)}"

    logger.info(
        f"Notification sent to {success_count}/{len(settings.TELEGRAM_ADMIN_IDS)} admins"
    )
    return {
        "total_admins": len(settings.TELEGRAM_ADMIN_IDS),
        "successful": success_count,
        "results": results,
    }


def notify_admin_login(username: str, ip_address: str = "Unknown") -> dict:
    """Send notification when an admin logs in."""
    message = f"🔐 <b>Admin Login Alert</b>\n\n👤 User: <code>{username}</code>\n🌐 IP: <code>{ip_address}</code>"
    return notify_admins(message)


def notify_new_registration(user_email: str, user_name: str = "Unknown") -> dict:
    """Send notification when a new user registers."""
    message = f"👋 <b>New User Registration</b>\n\n📧 Email: <code>{user_email}</code>\n👤 Name: <code>{user_name}</code>"
    return notify_admins(message)


def notify_new_booking(
    booking_id: str, user_email: str, package_name: str = "Unknown"
) -> dict:
    """Send notification when a new booking is made."""
    message = f"🎯 <b>New Booking Alert</b>\n\n📋 Booking ID: <code>{booking_id}</code>\n📧 User: <code>{user_email}</code>\n📦 Package: <code>{package_name}</code>"
    return notify_admins(message)


def notify_payment_received(amount: float, currency: str, booking_id: str) -> dict:
    """Send notification when a payment is received."""
    message = f"💰 <b>Payment Received</b>\n\n💵 Amount: <code>{amount} {currency}</code>\n📋 Booking: <code>{booking_id}</code>"
    return notify_admins(message)


def notify_system_error(error_message: str, context: str = "") -> dict:
    """Send notification for system errors."""
    message = f"🚨 <b>System Error Alert</b>\n\n❌ Error: <code>{error_message}</code>"
    if context:
        message += f"\n📍 Context: <code>{context}</code>"
    return notify_admins(message)


def test_telegram_connection() -> bool:
    """Test if the Telegram bot configuration is working."""
    bot_info = telegram_bot.get_me()
    if bot_info and bot_info.get("ok"):
        logger.info(
            f"Telegram bot connected successfully: {bot_info['result']['username']}"
        )
        return True
    else:
        logger.error("Failed to connect to Telegram bot")
        return False
