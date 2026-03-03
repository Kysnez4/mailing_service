from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone

from .models import Client, Message, Mailing, MailingAttempt
from .forms import ClientForm, MessageForm, MailingForm, CustomUserCreationForm
from .tasks import send_mailing_task
from user.models import User


class OwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        # Менеджер может только просматривать, не редактировать/удалять чужое
        if user.is_manager and self.request.method in ['GET']:
            return True
        return obj.user == user or user.is_staff


# Client Views
class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'mailing/client_list.html'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_manager:
            return Client.objects.all()
        return Client.objects.filter(user=user)


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'mailing/client_form.html'
    success_url = reverse_lazy('client_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'mailing/client_form.html'
    success_url = reverse_lazy('client_list')


class ClientDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Client
    template_name = 'mailing/client_confirm_delete.html'
    success_url = reverse_lazy('client_list')


# Message Views
class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'mailing/message_list.html'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_manager:
            return Message.objects.all()
        return Message.objects.filter(user=user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('message_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('message_list')


class MessageDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('message_list')


# Mailing Views
class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = 'mailing/mailing_list.html'

    def get_queryset(self):
        user = self.request.user
        queryset = Mailing.objects.all()
        if not (user.is_staff or user.is_manager):
            queryset = queryset.filter(user=user)
        return queryset.select_related('message').prefetch_related('clients')


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class MailingDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Mailing
    template_name = 'mailing/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailing_list')


class MailingDetailView(LoginRequiredMixin, OwnerRequiredMixin, DetailView):
    model = Mailing
    template_name = 'mailing/mailing_detail.html'


@login_required
def dashboard(request):
    cache_key = f'dashboard_stats_{request.user.id}'
    stats = cache.get(cache_key)

    if not stats:
        mailings = Mailing.objects.all()
        if not request.user.is_staff:
            mailings = mailings.filter(user=request.user)

        stats = {
            'total_mailings': mailings.count(),
            'active_mailings': mailings.filter(status='started').count(),
            'unique_clients': Client.objects.filter(user=request.user).count(),
        }
        cache.set(cache_key, stats, 300)  # Кешируем на 5 минут

    return render(request, 'mailing/dashboard.html', stats)


@login_required
def send_mailing_now(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    if mailing.user != request.user and not request.user.is_staff:
        messages.error(request, "У вас нет прав для отправки этой рассылки")
        return redirect('mailing_list')

    send_mailing_task.delay(mailing.id)
    messages.success(request, "Рассылка поставлена в очередь на отправку")
    return redirect('mailing_detail', pk=pk)


@login_required
def user_stats(request):
    from .models import Mailing, MailingAttempt
    user = request.user
    cache_key = f'user_stats_{user.id}_manager_{user.is_manager}'
    context = cache.get(cache_key)
    if not context:
        if user.is_manager or user.is_staff:
            mailings = Mailing.objects.all()
        else:
            mailings = Mailing.objects.filter(user=user)
        attempts = MailingAttempt.objects.filter(mailing__in=mailings)
        total_attempts = attempts.count()
        success_attempts = attempts.filter(status='success').count()
        failed_attempts = attempts.filter(status='failed').count()
        total_messages = mailings.count()
        # Для каждой рассылки считаем успешные/неуспешные попытки
        mailing_stats = []
        for mailing in mailings:
            attempts_qs = mailing.attempts.all()
            mailing_stats.append({
                'mailing': mailing,
                'total': attempts_qs.count(),
                'success': attempts_qs.filter(status='success').count(),
                'failed': attempts_qs.filter(status='failed').count(),
            })
        context = {
            'total_attempts': total_attempts,
            'success_attempts': success_attempts,
            'failed_attempts': failed_attempts,
            'total_messages': total_messages,
            'mailing_stats': mailing_stats,
        }
        cache.set(cache_key, context, 300)  # 5 минут
    return render(request, 'mailing/user_stats.html', context)


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Регистрация успешна! Теперь вы можете войти.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})