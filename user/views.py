# users
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.core.signing import Signer, BadSignature
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from mailing.models import Mailing

from mailing_service.settings import EMAIL_HOST_USER
from user.forms import RegisterUserForm, LoginUserForm


class CustomUserLogin(LoginView):
    template_name = 'users/login.html'
    success_url = reverse_lazy('home')
    form_class = LoginUserForm


class CustomUserLogout(LogoutView):
    next_page = reverse_lazy('home')


class RegisterView(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True  # пользователь активен, но email не подтверждён
        user.is_email_confirmed = False
        user.save()
        login(self.request, user)
        self.send_confirmation_email(user)
        return super().form_valid(form)

    def send_confirmation_email(self, user):
        signer = Signer()
        token = signer.sign(user.pk)
        confirm_url = self.request.build_absolute_uri(
            reverse_lazy('confirm_email', kwargs={'token': token})
        )
        subject = 'Подтверждение email'
        message = f'Пожалуйста, подтвердите ваш email, перейдя по ссылке: {confirm_url}'
        recipient_list = [user.email]
        send_mail(subject, message, EMAIL_HOST_USER, recipient_list, fail_silently=False)


def confirm_email(request, token):
    signer = Signer()
    try:
        user_pk = signer.unsign(token)
        from .models import User
        user = User.objects.get(pk=user_pk)
        user.is_email_confirmed = True
        user.save()
        return HttpResponse('Email успешно подтверждён! Теперь вы можете войти.')
    except (BadSignature, User.DoesNotExist):
        return HttpResponse('Некорректная или устаревшая ссылка подтверждения.', status=400)


def is_manager(user):
    return user.is_authenticated and user.is_manager

@user_passes_test(is_manager)
def user_list(request):
    from .models import User
    users = User.objects.all()
    return render(request, 'users/user_list.html', {'users': users})

@user_passes_test(is_manager)
def block_user(request, user_id):
    from .models import User
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        user.is_active = False
        user.save()
        return redirect('user_list')
    return render(request, 'users/block_user_confirm.html', {'user': user})

@user_passes_test(is_manager)
def disable_mailings(request, user_id):
    from .models import User
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        Mailing.objects.filter(user=user).update(status='completed')
        return redirect('user_list')
    return render(request, 'users/disable_mailings_confirm.html', {'user': user})
