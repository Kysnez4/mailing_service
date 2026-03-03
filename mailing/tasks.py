from mailing.models import Mailing, MailingAttempt
from django.utils import timezone

def send_mailing_task(mailing_id):
    try:
        mailing = Mailing.objects.get(pk=mailing_id)
    except Mailing.DoesNotExist:
        print(f"Рассылка {mailing_id} не найдена")
        return

    # Обновляем статус рассылки
    mailing.status = 'started'
    mailing.save()

    # Фиктивная отправка писем всем получателям
    for client in mailing.clients.all():
        # Здесь должна быть реальная отправка email через SMTP или другой сервис
        # Для примера считаем, что отправка всегда успешна
        status = 'success'
        server_response = f"Письмо отправлено на {client.email} (заглушка)"
        MailingAttempt.objects.create(
            mailing=mailing,
            status=status,
            server_response=server_response
        )
        print(server_response)

    print(f"Рассылка {mailing_id} завершена для {mailing.clients.count()} получателей.") 