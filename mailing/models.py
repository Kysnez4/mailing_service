from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator

from user.models import User


class Client(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(
        verbose_name="ФИО",
        max_length=255,
        validators=[MinLengthValidator(3)]
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.full_name} ({self.email})'

    class Meta:
        verbose_name = 'Получатель'
        verbose_name_plural = 'Получатели'
        ordering = ['email']
        permissions = [
            ("can_view_all_clients", "Может просматривать всех получателей"),
        ]


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    subject = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        permissions = [
            ("can_view_all_messages", "Может просматривать все сообщения"),
        ]


class Mailing(models.Model):
    STATUS_CHOICES = (
        ('created', 'Создана'),
        ('started', 'Запущена'),
        ('completed', 'Завершена')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mailings')
    start_time = models.DateTimeField(verbose_name="Время начала")
    end_time = models.DateTimeField(verbose_name="Время окончания")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='created',
        verbose_name="Статус"
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        verbose_name="Сообщение"
    )
    clients = models.ManyToManyField(Client, verbose_name="Получатели")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Рассылка #{self.id} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        # Автоматическое обновление статуса если время окончания прошло
        if self.end_time < timezone.now() and self.status != 'completed':
            self.status = 'completed'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ['-created_at']
        permissions = [
            ("can_view_all_mailings", "Может просматривать все рассылки"),
            ("can_disable_mailings", "Может отключать рассылки"),
        ]


class MailingAttempt(models.Model):
    STATUS_CHOICES = (
        ('success', 'Успешно'),
        ('failed', 'Не успешно'),
    )
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name="Рассылка"
    )
    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name="Время попытки")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        verbose_name="Статус попытки"
    )
    server_response = models.TextField(verbose_name="Ответ сервера")

    def __str__(self):
        return f"Попытка #{self.id} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылки"
        ordering = ['-attempt_time']
        permissions = [
            ("can_view_all_attempts", "Может просматривать все попытки рассылки"),
        ]