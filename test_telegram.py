#!/usr/bin/env python3
"""
Test script for Telegram bot configuration.
Run this script to test if your Telegram bot is working correctly.
"""

import asyncio

from app.core.config import settings
from app.core.telegram import (
    notify_admin_login,
    notify_admins,
    notify_new_booking,
    notify_new_registration,
    notify_payment_received,
    notify_system_error,
    test_telegram_connection,
)


def main():
    print("🤖 Testing Telegram Bot Configuration")
    print("=" * 50)

    # Display current configuration
    print(
        f"📋 Bot Token: {'✅ Configured' if settings.TELEGRAM_BOT_TOKEN else '❌ Missing'}"
    )
    print(f"👥 Admin IDs: {settings.TELEGRAM_ADMIN_IDS}")
    print(f"📊 Total Admins: {len(settings.TELEGRAM_ADMIN_IDS)}")
    print()

    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN is not configured in your .env file")
        return

    if not settings.TELEGRAM_ADMIN_IDS:
        print("❌ TELEGRAM_ADMIN_IDS is not configured in your .env file")
        return

    # Test bot connection
    print("🔌 Testing bot connection...")
    if test_telegram_connection():
        print("✅ Bot connection successful!")
    else:
        print("❌ Bot connection failed! Check your bot token.")
        return

    print()

    # Test basic notification
    print("📤 Testing basic notification...")
    result = notify_admins("🧪 Test message from Global Divers backend!")
    print(f"✅ Notification result: {result}")
    print()

    # Test specific notification types
    print("📤 Testing admin login notification...")
    result = notify_admin_login("test_admin", "192.168.1.1")
    print(f"✅ Login notification result: {result}")
    print()

    print("📤 Testing new registration notification...")
    result = notify_new_registration("test@example.com", "Test User")
    print(f"✅ Registration notification result: {result}")
    print()

    print("📤 Testing new booking notification...")
    result = notify_new_booking(
        "BOOK123", "customer@example.com", "Scuba Diving Course"
    )
    print(f"✅ Booking notification result: {result}")
    print()

    print("📤 Testing payment notification...")
    result = notify_payment_received(250.00, "USD", "BOOK123")
    print(f"✅ Payment notification result: {result}")
    print()

    print("📤 Testing error notification...")
    result = notify_system_error("Database connection timeout", "User authentication")
    print(f"✅ Error notification result: {result}")
    print()

    print("🎉 All tests completed!")


if __name__ == "__main__":
    main()
