from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    MANAGER = 'manager'
    SUPERVISOR = 'supervisor'
    EXPERT = 'expert'

    ROLE_CHOICES = [
        (MANAGER, 'مدیر کل فروش'),
        (SUPERVISOR, 'سوپروایزر'),
        (EXPERT, 'کارشناس'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=EXPERT,
        verbose_name='نقش'
    )
    supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_members',
        verbose_name='سوپروایزر',
    )
    phone = models.CharField(max_length=15, blank=True, verbose_name='شماره تماس')
    is_online = models.BooleanField(default=False, verbose_name='آنلاین')
    max_capacity = models.PositiveIntegerField(default=20, verbose_name='ظرفیت حداکثر لید')
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='تصویر پروفایل'
    )
    bio = models.TextField(blank=True, verbose_name='بیوگرافی')

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        full = self.get_full_name()
        return f"{full or self.username} ({self.get_role_display()})"

    @property
    def is_manager(self):
        return self.role == self.MANAGER

    @property
    def is_supervisor(self):
        return self.role == self.SUPERVISOR

    @property
    def is_expert(self):
        return self.role == self.EXPERT

    @property
    def full_name_or_username(self):
        return self.get_full_name() or self.username

    @property
    def current_lead_count(self):
        return self.assigned_leads.filter(status__in=['new', 'contacted', 'interested']).count()

    def get_team_experts(self):
        if self.is_supervisor:
            return User.objects.filter(supervisor=self, role=self.EXPERT, is_active=True)
        return User.objects.none()

    def get_visible_users(self):
        if self.is_manager:
            return User.objects.filter(is_active=True).exclude(pk=self.pk)
        elif self.is_supervisor:
            return User.objects.filter(supervisor=self, role=self.EXPERT, is_active=True)
        return User.objects.none()
