from django.core.management.base import BaseCommand, CommandError
from mailing.models import Mailing
from mailing.tasks import send_mailing_task

class Command(BaseCommand):
    help = 'Отправить рассылку по её id (pk)'

    def add_arguments(self, parser):
        parser.add_argument('mailing_id', type=int, help='ID рассылки')

    def handle(self, *args, **options):
        mailing_id = options['mailing_id']
        try:
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist:
            raise CommandError(f'Рассылка с id={mailing_id} не найдена')
        send_mailing_task.delay(mailing.id)
        self.stdout.write(self.style.SUCCESS(f'Рассылка {mailing_id} поставлена в очередь на отправку')) 