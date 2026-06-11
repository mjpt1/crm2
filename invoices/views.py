from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.models import User
from leads.models import Lead
from .models import Invoice
from .forms import InvoiceForm
from .zibal_service import ZibalService


def _get_invoices_qs(user):
    if user.is_manager:
        return Invoice.objects.select_related('lead', 'expert').all()
    elif user.is_supervisor:
        team = user.team_members.filter(role=User.EXPERT)
        return Invoice.objects.select_related('lead', 'expert').filter(expert__in=team)
    return Invoice.objects.select_related('lead', 'expert').filter(expert=user)


@login_required
def invoice_list(request):
    qs = _get_invoices_qs(request.user)

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    totals = {
        'pending': _get_invoices_qs(request.user).filter(status='pending').count(),
        'paid': _get_invoices_qs(request.user).filter(status='paid').count(),
    }

    return render(request, 'invoices/invoice_list.html', {
        'invoices': qs,
        'status_choices': Invoice.STATUS_CHOICES,
        'current_status': status_filter,
        'totals': totals,
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(_get_invoices_qs(request.user), pk=pk)
    return render(request, 'invoices/invoice_detail.html', {'invoice': invoice})


@login_required
def invoice_create(request):
    form = InvoiceForm(request.POST or None, requesting_user=request.user)
    if request.method == 'POST' and form.is_valid():
        invoice = form.save(commit=False)
        invoice.expert = request.user if request.user.is_expert else form.cleaned_data['lead'].assigned_to or request.user
        invoice.save()

        # اگر لید بعد از ثبت فاکتور تبدیل شد، وضعیت آن را به‌روز کن
        lead = invoice.lead
        if lead.status not in (Lead.CONVERTED, Lead.LOST):
            lead.status = Lead.INTERESTED
            lead.save(update_fields=['status'])

        messages.success(request, f'فاکتور {invoice.invoice_number} صادر شد.')
        return redirect('invoices:detail', pk=invoice.pk)

    return render(request, 'invoices/invoice_form.html', {
        'form': form,
        'action': 'صدور فاکتور جدید',
    })


@login_required
def invoice_approve(request, pk):
    """تایید مالی فاکتور — فقط مدیر یا سوپروایزر"""
    if request.user.is_expert:
        return HttpResponseForbidden()
    invoice = get_object_or_404(_get_invoices_qs(request.user), pk=pk)
    if invoice.status == Invoice.PENDING:
        invoice.status = Invoice.APPROVED
        invoice.save(update_fields=['status'])
        messages.success(request, f'فاکتور {invoice.invoice_number} تایید مالی شد.')
    return redirect('invoices:detail', pk=pk)


@login_required
def invoice_cancel(request, pk):
    if request.user.is_expert:
        return HttpResponseForbidden()
    invoice = get_object_or_404(_get_invoices_qs(request.user), pk=pk)
    if invoice.status not in (Invoice.PAID, Invoice.CANCELLED):
        invoice.status = Invoice.CANCELLED
        invoice.save(update_fields=['status'])
        messages.warning(request, f'فاکتور {invoice.invoice_number} ابطال شد.')
    return redirect('invoices:detail', pk=pk)


@login_required
def send_payment_link(request, pk):
    """ایجاد لینک پرداخت زیبال و ارسال به مشتری"""
    invoice = get_object_or_404(_get_invoices_qs(request.user), pk=pk)

    if invoice.status not in (Invoice.PENDING, Invoice.APPROVED):
        messages.error(request, 'امکان ارسال لینک برای این فاکتور وجود ندارد.')
        return redirect('invoices:detail', pk=pk)

    svc = ZibalService()
    result = svc.request_payment(
        amount_toman=invoice.amount,
        order_id=invoice.invoice_number,
        description=invoice.description or f'فاکتور {invoice.invoice_number}',
        mobile=invoice.lead.phone,
        email=invoice.lead.email,
    )

    if result['success']:
        invoice.zibal_track_id = result['track_id']
        invoice.payment_url = result['payment_url']
        invoice.save(update_fields=['zibal_track_id', 'payment_url'])
        messages.success(request, f'لینک پرداخت ایجاد شد: {result["payment_url"]}')
    else:
        messages.error(request, f'خطا در ایجاد لینک: {result["error"]}')

    return redirect('invoices:detail', pk=pk)


def payment_callback(request):
    """بازگشت از درگاه زیبال پس از پرداخت مشتری"""
    track_id = request.GET.get('trackId', '')
    success = request.GET.get('success', '0')
    order_id = request.GET.get('orderId', '')

    context = {'track_id': track_id, 'order_id': order_id}

    if success != '1' or not track_id:
        context['error'] = 'پرداخت ناموفق یا لغو شده است.'
        return render(request, 'invoices/payment_result.html', context)

    try:
        invoice = Invoice.objects.get(invoice_number=order_id)
    except Invoice.DoesNotExist:
        context['error'] = 'فاکتور مربوطه یافت نشد.'
        return render(request, 'invoices/payment_result.html', context)

    if invoice.status == Invoice.PAID:
        context['already_paid'] = True
        return render(request, 'invoices/payment_result.html', context)

    svc = ZibalService()
    verify = svc.verify_payment(track_id)

    if verify['success']:
        invoice.status = Invoice.PAID
        invoice.paid_at = timezone.now()
        invoice.ref_number = verify.get('ref_number', '')
        invoice.save(update_fields=['status', 'paid_at', 'ref_number'])

        invoice.lead.status = Lead.CONVERTED
        invoice.lead.save(update_fields=['status'])

        context['verified'] = True
        context['ref_number'] = verify.get('ref_number')
        context['invoice'] = invoice
    else:
        context['error'] = verify.get('error', 'خطا در تایید پرداخت.')

    return render(request, 'invoices/payment_result.html', context)


@csrf_exempt
@require_POST
def zibal_webhook(request):
    """Webhook زیبال — بروزرسانی لحظه‌ای وضعیت فاکتور"""
    import json
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'status': 'error'}, status=400)

    track_id = str(data.get('trackId', ''))
    status = data.get('status')

    if status == 1 and track_id:
        try:
            invoice = Invoice.objects.get(zibal_track_id=track_id)
            if invoice.status != Invoice.PAID:
                svc = ZibalService()
                verify = svc.verify_payment(track_id)
                if verify['success']:
                    invoice.status = Invoice.PAID
                    invoice.paid_at = timezone.now()
                    invoice.ref_number = verify.get('ref_number', '')
                    invoice.save(update_fields=['status', 'paid_at', 'ref_number'])
                    invoice.lead.status = Lead.CONVERTED
                    invoice.lead.save(update_fields=['status'])
        except Invoice.DoesNotExist:
            pass

    return JsonResponse({'status': 'ok'})
