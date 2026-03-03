from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Client, Message, Mailing

class ClientForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите email',
        }),
        help_text='Укажите уникальный email.'
    )
    full_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ФИО',
        }),
        help_text='Фамилия Имя Отчество.'
    )
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Комментарий',
            'rows': 3,
        }),
        help_text='Дополнительная информация.'
    )
    class Meta:
        model = Client
        fields = ['email', 'full_name', 'comment']

    def clean_email(self):
        email = self.cleaned_data['email']
        if Client.objects.filter(email=email).exists():
            raise ValidationError("Клиент с таким email уже существует")
        return email

class MessageForm(forms.ModelForm):
    subject = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Тема письма',
        }),
        help_text='Кратко опишите тему письма.'
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Текст письма',
            'rows': 5,
        }),
        help_text='Основной текст письма.'
    )
    class Meta:
        model = Message
        fields = ['subject', 'body']

class MailingForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].queryset = Message.objects.filter(user=user)
        self.fields['clients'].queryset = Client.objects.filter(user=user)
        self.fields['message'].widget.attrs.update({'class': 'form-control'})
        self.fields['clients'].widget.attrs.update({'class': 'form-control'})
        self.fields['start_time'].widget.attrs.update({'class': 'form-control', 'type': 'datetime-local'})
        self.fields['end_time'].widget.attrs.update({'class': 'form-control', 'type': 'datetime-local'})

    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'message', 'clients']
        widgets = {
            'start_time': forms.DateTimeInput(),
            'end_time': forms.DateTimeInput(),
            'clients': forms.SelectMultiple(),
        }
        help_texts = {
            'start_time': 'Дата и время первой отправки.',
            'end_time': 'Дата и время окончания отправки.',
            'message': 'Выберите сообщение для рассылки.',
            'clients': 'Выберите получателей рассылки.',
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)