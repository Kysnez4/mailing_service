#users
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.utils.translation import gettext_lazy as _

from user.models import User


class LoginUserForm(AuthenticationForm):
    error_messages = {
        'invalid_login': _('Пожалуйста, введите правильный email и пароль. Оба поля чувствительны к регистру.'),
        'inactive': _('Этот аккаунт неактивен.'),
    }
    def confirm_login_allowed(self, user):
        if not user.is_email_confirmed:
            raise forms.ValidationError('Вы должны подтвердить email для входа.', code='email_not_confirmed')

    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя',
        })
    )

    password = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль',
        })
    )

    class Meta:
        model = User
        fields = ('username', 'password')


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя',
        }),
        help_text='Обязательное поле. Только буквы, цифры и символы @/./+/-/_.'
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email',
        }),
        help_text='Укажите действующий email.'
    )
    phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите номер телефона',
        }),
        help_text='Только цифры.'
    )
    country = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите страну',
        }),
        help_text='Страна проживания.'
    )

    class Meta:
        model = User
        fields = ('username','email', 'phone', 'country', 'avatar', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль',
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Подтвердите пароль',
        })
        self.fields['password1'].help_text = 'Пароль должен содержать минимум 8 символов.'
        self.fields['password2'].help_text = 'Повторите пароль.'
        self.fields['username'].help_text = 'Обязательное поле. Только буквы, цифры и символы @/./+/-/_.'

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if phone and not phone.isdigit():
            raise forms.ValidationError('Номер телефона должен содержать только цифры')
        return phone