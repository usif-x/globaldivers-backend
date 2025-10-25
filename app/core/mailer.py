import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


class EmailSender:
    """Email sender using SMTP"""

    @staticmethod
    def render_template(template_name: str, context: Dict[str, str]) -> str:
        """
        Render an email template with the given context.

        Args:
            template_name: Name of the template file
            context: Dictionary of variables to replace in the template

        Returns:
            str: Rendered HTML content
        """
        template_path = TEMPLATE_DIR / template_name

        if not template_path.exists():
            logger.error(f"Template not found: {template_path}")
            raise FileNotFoundError(f"Template {template_name} not found")

        # Read template
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        # Simple template variable replacement - try both with and without spaces
        for key, value in context.items():
            # Replace {{ key }} (with spaces)
            template_content = template_content.replace(f"{{{{ {key} }}}}", str(value))
            # Replace {{key}} (without spaces)
            template_content = template_content.replace(f"{{{{{key}}}}}", str(value))

        logger.info(f"Template {template_name} rendered successfully")
        return template_content

    @staticmethod
    def send_email(
        to_email: str | List[str],
        subject: str,
        message: str = "",
        html_message: Optional[str] = None,
        template_name: Optional[str] = None,
        context: Optional[Dict[str, str]] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Send an email using SMTP.

        Args:
            to_email: Recipient email address or list of addresses
            subject: Email subject
            message: Plain text message (optional if using template)
            html_message: Optional HTML version of the message
            template_name: Optional template file name to use
            context: Optional context dictionary for template rendering
            from_email: Optional custom from email (default: from settings)
            from_name: Optional custom from name (default: from settings)

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Convert single email to list
            if isinstance(to_email, str):
                recipients = [to_email]
            else:
                recipients = to_email

            # Use default from email and name if not provided
            sender_email = from_email or settings.EMAIL_FROM
            sender_name = from_name or settings.EMAIL_FROM_NAME

            # Render template if provided
            if template_name and context:
                logger.info(
                    f"Rendering template: {template_name} with context: {context}"
                )
                html_message = EmailSender.render_template(template_name, context)
                # Generate plain text from context if message not provided
                if not message:
                    message = f"Welcome {context.get('full_name', 'User')}! Please view this email in an HTML-capable email client."
                logger.info("Template rendered and HTML message prepared")

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{sender_name} <{sender_email}>"
            msg["To"] = ", ".join(recipients)

            # Add plain text part
            if message:
                text_part = MIMEText(message, "plain", "utf-8")
                msg.attach(text_part)
                logger.info("Plain text part attached")

            # Add HTML part if provided
            if html_message:
                html_part = MIMEText(html_message, "html", "utf-8")
                msg.attach(html_part)
                logger.info("HTML part attached")

            # Connect to SMTP server and send email
            if settings.EMAIL_USE_SSL:
                # Use SSL connection
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    server.sendmail(sender_email, recipients, msg.as_string())
            else:
                # Use TLS connection
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    if settings.EMAIL_USE_TLS:
                        server.starttls()  # Enable TLS encryption
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    server.sendmail(sender_email, recipients, msg.as_string())

            logger.info(f"Email sent successfully to {recipients}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    @staticmethod
    def send_bulk_email(
        recipients: List[str],
        subject: str,
        message: str,
        html_message: Optional[str] = None,
    ) -> dict:
        """
        Send email to multiple recipients individually.

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            message: Plain text message
            html_message: Optional HTML version of the message

        Returns:
            dict: Dictionary with 'success' count and 'failed' list
        """
        success_count = 0
        failed_emails = []

        for email in recipients:
            if EmailSender.send_email(email, subject, message, html_message):
                success_count += 1
            else:
                failed_emails.append(email)

        return {"success": success_count, "failed": failed_emails}


# Initialize email sender instance
email_sender = EmailSender()


# Convenience function for quick email sending
def send_email(
    to_email: str | List[str],
    subject: str,
    message: str = "",
    html_message: Optional[str] = None,
    template_name: Optional[str] = None,
    context: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Quick function to send an email.

    Args:
        to_email: Recipient email address or list of addresses
        subject: Email subject
        message: Plain text message (optional if using template)
        html_message: Optional HTML version of the message
        template_name: Optional template file name to use
        context: Optional context dictionary for template rendering

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    return email_sender.send_email(
        to_email, subject, message, html_message, template_name, context
    )
