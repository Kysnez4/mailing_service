#users
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars', null=True, blank=True)
    phone = models.CharField(max_length=11, unique=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    is_email_confirmed = models.BooleanField(default=False, verbose_name='Email подтверждён')
    is_manager = models.BooleanField(default=False, verbose_name='Менеджер')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta(AbstractUser.Meta):
        permissions = [
            ("can_block_users", "Может блокировать пользователей"),
            ("can_view_all_users", "Может просматривать всех пользователей"),
        ]

    def __str__(self):
        return self.email

