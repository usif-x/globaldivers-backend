"""
Test script for email functionality
Run with: python test_email.py
"""

from app.core.mailer import send_email


def test_welcome_email():
    """Test sending welcome email with template"""

    print("Testing welcome email with template...")

    result = send_email(
        to_email="yousseifmuhammed@gmail.com",  # Replace with your email to test
        subject="Welcome to Top Divers Hurghada!",
        template_name="welcome_email.html",
        context={"full_name": "John Doe"},
    )

    if result:
        print("✅ Email sent successfully!")
        print(f"Result: {result}")
    else:
        print("❌ Failed to send email. Check logs for details.")

    return result


def test_simple_email():
    """Test sending simple email without template"""

    print("\nTesting simple email...")

    result = send_email(
        to_email="yousseifmuhammed@gmail.com",  # Replace with your email to test
        subject="Test Email",
        message="This is a plain text test message.",
        html_message="<h1>This is an HTML test message</h1><p>Hello from Top Divers!</p>",
    )

    if result:
        print("✅ Email sent successfully!")
    else:
        print("❌ Failed to send email. Check logs for details.")

    return result


if __name__ == "__main__":
    print("=" * 50)
    print("Email System Test")
    print("=" * 50)

    # Test 1: Welcome email with template
    test_welcome_email()

    # Test 2: Simple email
    test_simple_email()

    print("\n" + "=" * 50)
    print("Tests completed!")
    print("=" * 50)
