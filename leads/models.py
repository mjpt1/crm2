import uuid
from django.db import models
from accounts.models import User


class UTMSource(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام کمپین')
    utm_source = models.CharField(max_length=100, verbose_name='منبع')
    utm_medium = models.CharField(max_length=100, blank=True, verbose_name='رسانه')
    utm_campaign = models.CharField(max_length=100, blank=True, verbose_name='کمپین')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name='توکن')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'منبع UTM'
        verbose_name_plural = 'منابع UTM'

    def __str__(self):
        return self.name

    @property
    def capture_path(self):
        return f"/leads/capture/{self.token}/"


class Lead(models.Model):
    NEW = 'new'
    CONTACTED = 'contacted'
    INTERESTED = 'interested'
    CONVERTED = 'converted'
    LOST = 'lost'

    STATUS_CHOICES = [
        (NEW, 'جدید'),
        (CONTACTED, 'تماس گرفته شده'),
        (INTERESTED, 'علاقه‌مند'),
        (CONVERTED, 'تبدیل شده به مشتری'),
        (LOST, 'از دست رفته'),
    ]

    STATUS_COLORS = {
        NEW: 'primary',
        CONTACTED: 'info',
        INTERESTED: 'warning',
        CONVERTED: 'success',
        LOST: 'danger',
    }

    name = models.CharField(max_length=200, verbose_name='نام و نام خانوادگی')
    phone = models.CharField(max_length=15, verbose_name='شماره تماس')
    email = models.EmailField(blank=True, verbose_name='ایمیل')
    company = models.CharField(max_length=200, blank=True, verbose_name='شرکت')

    utm_source = models.ForeignKey(
        UTMSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='منبع تبلیغاتی',
        related_name='leads'
    )
    source_detail = models.CharField(max_length=200, blank=True, verbose_name='جزئیات منبع')

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads',
        verbose_name='کارشناس'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=NEW,
        verbose_name='وضعیت'
    )
    notes = models.TextField(blank=True, verbose_name='یادداشت')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'سرنخ'
        verbose_name_plural = 'سرنخ‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.phone}"

    @property
    def status_color(self):
        return self.STATUS_COLORS.get(self.status, 'secondary')

    @property
    def has_paid_invoice(self):
        return self.invoices.filter(status='paid').exists()


class LeadNote(models.Model):
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='lead_notes',
        verbose_name='سرنخ'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='نویسنده'
    )
    content = models.TextField(verbose_name='متن یادداشت')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'یادداشت'
        verbose_name_plural = 'یادداشت‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"یادداشت برای {self.lead.name}"
