import jdatetime
from django.db import models
from django.utils import timezone
from accounts.models import User
from leads.models import Lead


class Invoice(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    PAID = 'paid'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (PENDING, 'در انتظار پرداخت'),
        (APPROVED, 'تایید مالی'),
        (PAID, 'وصول شده'),
        (CANCELLED, 'ابطال شده'),
    ]

    STATUS_COLORS = {
        PENDING: 'warning',
        APPROVED: 'info',
        PAID: 'success',
        CANCELLED: 'danger',
    }

    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='شماره فاکتور'
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.PROTECT,
        related_name='invoices',
        verbose_name='سرنخ'
    )
    expert = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='expert_invoices',
        verbose_name='کارشناس'
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name='مبلغ (تومان)'
    )
    description = models.TextField(blank=True, verbose_name='شرح')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        verbose_name='وضعیت'
    )

    zibal_track_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='کد پیگیری زیبال'
    )
    payment_url = models.URLField(blank=True, verbose_name='لینک پرداخت')
    ref_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='شماره مرجع بانکی'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ صدور')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پرداخت')

    class Meta:
        verbose_name = 'فاکتور'
        verbose_name_plural = 'فاکتورها'
        ordering = ['-created_at']

    def __str__(self):
        return f"فاکتور {self.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self._generate_number()
        super().save(*args, **kwargs)

    def _generate_number(self):
        now = jdatetime.datetime.now()
        prefix = f"INV-{now.strftime('%Y%m')}"
        last = Invoice.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-id').first()
        seq = (int(last.invoice_number.split('-')[-1]) + 1) if last else 1
        return f"{prefix}-{seq:04d}"

    @property
    def status_color(self):
        return self.STATUS_COLORS.get(self.status, 'secondary')

    @property
    def amount_formatted(self):
        return f"{int(self.amount):,}"
