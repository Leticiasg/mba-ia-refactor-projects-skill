"""Envio de notificações por e-mail (SMTP). Desligado enquanto SMTP_HOST não estiver configurado."""
import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    @classmethod
    def from_config(cls, config):
        return cls(config['SMTP_HOST'], config['SMTP_PORT'], config['SMTP_USER'], config['SMTP_PASSWORD'])

    @property
    def enabled(self):
        return bool(self.host and self.user)

    def send_email(self, recipient, subject, body):
        if not self.enabled:
            logger.debug("SMTP não configurado; e-mail '%s' não enviado.", subject)
            return False
        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = self.user
        message['To'] = recipient
        message.set_content(body)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            logger.exception("Falha ao enviar e-mail '%s'", subject)
            return False
        logger.info("E-mail '%s' enviado", subject)
        return True

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        return self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        return self.send_email(user.email, subject, body)
