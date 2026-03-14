import logging

from app.config import settings

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, token: str) -> None:
    verify_url = f"{settings.MAIL_FROM.replace('@', 'verify-')}/verify?token={token}"
    body = f"Click to verify your email: {verify_url}"
    _send_email(to_email, "Verify your email", body)


def send_password_reset_email(to_email: str, token: str) -> None:
    reset_url = f"{settings.MAIL_FROM.replace('@', 'reset-')}/reset?token={token}"
    body = f"Click to reset your password: {reset_url}"
    _send_email(to_email, "Reset your password", body)


def send_invitation_email(
    to_email: str, org_name: str, inviter_name: str | None, token: str
) -> None:
    inviter = inviter_name or "A team member"
    accept_url = f"{settings.MAIL_FROM.replace('@', 'invite-')}/invite/accept?token={token}"
    body = f"{inviter} invited you to join {org_name}. Accept here: {accept_url}"
    _send_email(to_email, f"You're invited to join {org_name}", body)


def _send_email(to: str, subject: str, body: str) -> None:
    if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            msg = MIMEMultipart()
            msg["From"] = settings.MAIL_FROM
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            logger.info("Email sent to %s", to)
        except Exception as e:
            logger.exception("Failed to send email to %s: %s", to, e)
    else:
        logger.info("[DEV] Email would send to %s: %s - %s", to, subject, body[:80])
