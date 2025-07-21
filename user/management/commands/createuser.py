from django.core.management.base import BaseCommand
from user.models import User

class Command(BaseCommand):
    help = 'Создать пользователя (email, username, пароль, опционально менеджер)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email пользователя')
        parser.add_argument('username', type=str, help='Имя пользователя')
        parser.add_argument('password', type=str, help='Пароль')
        parser.add_argument('--manager', action='store_true', help='Создать пользователя как менеджера')

    def handle(self, *args, **options):
        email = options['email']
        username = options['username']
        password = options['password']
        is_manager = options['manager']
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR('Пользователь с таким email уже существует.'))
            return
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR('Пользователь с таким именем уже существует.'))
            return
        user = User.objects.create_user(email=email, username=username, password=password, is_manager=is_manager)
        user.is_active = True
        user.is_email_confirmed = True
        user.save()
        self.stdout.write(self.style.SUCCESS(f'Пользователь {email} успешно создан.')) 