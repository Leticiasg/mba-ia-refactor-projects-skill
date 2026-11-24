"""Notificações por e-mail (SMTP). Sem SMTP configurado no ambiente, nada é enviado."""
import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 10


class NotificationService:
    def __init__(self, host, port, user, password, sender):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.sender = sender

    @classmethod
    def from_config(cls, config):
        return cls(config['SMTP_HOST'], config['SMTP_PORT'], config['SMTP_USER'],
                   config['SMTP_PASSWORD'], config['SMTP_SENDER'])

    def is_configured(self):
        return bool(self.host and self.user and self.password and self.sender)

    def send_email(self, recipient, subject, body):
        if not self.is_configured():
            logger.debug('SMTP não configurado; notificação "%s" não enviada', subject)
            return False
        message = EmailMessage()
        message['From'] = self.sender
        message['To'] = recipient
        message['Subject'] = subject
        message.set_content(body)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=SMTP_TIMEOUT_SECONDS) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            logger.exception('Falha ao enviar notificação "%s"', subject)
            return False
        logger.info('Notificação "%s" enviada', subject)
        return True

    def notify_task_assigned(self, user, task):
        subject = f'Nova task atribuída: {task.title}'
        body = (f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
                f'Prioridade: {task.priority}\nStatus: {task.status}')
        return self.send_email(user.email, subject, body)
