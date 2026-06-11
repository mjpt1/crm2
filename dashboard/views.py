import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from leads.models import Lead
from invoices.models import Invoice


def _expert_scope(user):
    """بازه کارشناسان قابل مشاهده برای هر نقش"""
    if user.is_manager:
        return User.objects.filter(role=User.EXPERT, is_active=True)
    elif user.is_supervisor:
        return user.team_members.filter(role=User.EXPERT, is_active=True)
    return User.objects.filter(pk=user.pk)


def _invoice_scope(user):
    if user.is_manager:
        return Invoice.objects.all()
    elif user.is_supervisor:
        team = user.team_members.filter(role=User.EXPERT)
        return Invoice.objects.filter(expert__in=team)
    return Invoice.objects.filter(expert=user)


def _lead_scope(user):
    if user.is_manager:
        return Lead.objects.all()
    elif user.is_supervisor:
        team = user.team_members.filter(role=User.EXPERT)
        return Lead.objects.filter(assigned_to__in=team)
    return Lead.objects.filter(assigned_to=user)


@login_required
def index(request):
    today = timezone.localdate()
    this_month_start = today.replace(day=1)

    invoices = _invoice_scope(request.user)
    leads = _lead_scope(request.user)
    experts = _expert_scope(request.user)

    # ─── کارت‌های خلاصه ───
    today_sales = invoices.filter(status='paid', paid_at__date=today).aggregate(
        total=Sum('amount'), count=Count('id')
    )
    month_sales = invoices.filter(status='paid', paid_at__date__gte=this_month_start).aggregate(
        total=Sum('amount'), count=Count('id')
    )
    total_leads = leads.count()
    converted_leads = leads.filter(status='converted').count()
    conversion_rate = round((converted_leads / total_leads * 100) if total_leads else 0, 1)

    # ─── نمودار رقابتی کارشناسان (ماه جاری) ───
    expert_stats = []
    for expert in experts.select_related('supervisor'):
        paid_qs = invoices.filter(expert=expert, status='paid', paid_at__date__gte=this_month_start)
        total = paid_qs.aggregate(t=Sum('amount'))['t'] or 0
        count = paid_qs.count()

        # Delta Time: فاصله اولین تا آخرین فاکتور روز
        today_invoices = invoices.filter(
            expert=expert, status='paid', paid_at__date=today
        ).order_by('paid_at')
        delta_minutes = 0
        if today_invoices.count() >= 2:
            first = today_invoices.first().paid_at
            last = today_invoices.last().paid_at
            delta_minutes = int((last - first).total_seconds() // 60)

        lead_count = leads.filter(assigned_to=expert).count()
        conv = leads.filter(assigned_to=expert, status='converted').count()
        conv_rate = round((conv / lead_count * 100) if lead_count else 0, 1)

        expert_stats.append({
            'expert': expert,
            'total': int(total),
            'count': count,
            'lead_count': lead_count,
            'conversion_rate': conv_rate,
            'delta_minutes': delta_minutes,
        })

    expert_stats.sort(key=lambda x: x['total'], reverse=True)
    top3 = expert_stats[:3]

    # ─── داده نمودار میله‌ای Chart.js ───
    chart_labels = [s['expert'].full_name_or_username for s in expert_stats[:10]]
    chart_data = [s['total'] for s in expert_stats[:10]]

    # ─── نمودار روند ۳۰ روزه فروش ───
    trend_data = []
    trend_labels = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        amount = invoices.filter(
            status='paid', paid_at__date=d
        ).aggregate(t=Sum('amount'))['t'] or 0
        trend_labels.append(str(d))
        trend_data.append(int(amount))

    # ─── وضعیت لیدها (دونات) ───
    lead_status_data = [
        leads.filter(status=Lead.NEW).count(),
        leads.filter(status=Lead.CONTACTED).count(),
        leads.filter(status=Lead.INTERESTED).count(),
        leads.filter(status=Lead.CONVERTED).count(),
        leads.filter(status=Lead.LOST).count(),
    ]

    return render(request, 'dashboard/index.html', {
        'today_sales': today_sales,
        'month_sales': month_sales,
        'total_leads': total_leads,
        'converted_leads': converted_leads,
        'conversion_rate': conversion_rate,
        'expert_stats': expert_stats,
        'top3': top3,
        'chart_labels_json': json.dumps(chart_labels, ensure_ascii=False),
        'chart_data_json': json.dumps(chart_data),
        'trend_labels_json': json.dumps(trend_labels),
        'trend_data_json': json.dumps(trend_data),
        'lead_status_json': json.dumps(lead_status_data),
        'today': today,
    })
