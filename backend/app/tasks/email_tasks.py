"""
Email Tasks

Background tasks for sending emails.

TODO: Implement Celery tasks for:
- Welcome emails for new users
- Password reset emails
- Warning notifications for abnormalities
- Daily/weekly report delivery
- System alerts
"""

# Example Celery task (when implemented):
#
# from celery import shared_task
# from app.core.config import settings
# import aiosmtplib
# from email.message import EmailMessage
#
# @shared_task
# async def send_welcome_email(user_email: str, user_name: str):
#     """Send welcome email to new user"""
#     msg = EmailMessage()
#     msg['Subject'] = 'Welcome to SENTINEL'
#     msg['From'] = settings.SMTP_FROM_EMAIL
#     msg['To'] = user_email
#     msg.set_content(f'Hello {user_name},\n\nWelcome to SENTINEL!')
#     
#     await aiosmtplib.send(
#         msg,
#         hostname=settings.SMTP_HOST,
#         port=settings.SMTP_PORT,
#         username=settings.SMTP_USER,
#         password=settings.SMTP_PASSWORD
#     )
#
# @shared_task
# async def send_abnormality_warning(
#     user_email: str,
#     abnormality_type: str,
#     session_id: str
# ):
#     """Send warning email for detected abnormality"""
#     # TODO: Implement warning email
#     pass
#
# @shared_task
# async def send_weekly_report(user_email: str, report_data: dict):
#     """Send weekly productivity report"""
#     # TODO: Generate and send report
#     pass


# Temporary: Simple email function (non-Celery)
async def send_simple_email(to: str, subject: str, body: str):
    """
    Simple email sender (not background task)
    Use this until Celery is set up
    """
    # TODO: Implement with aiosmtplib
    print(f"Email: {to} - {subject}")
    print(f"Body: {body}")