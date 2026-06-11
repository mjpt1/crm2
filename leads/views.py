from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from .models import Lead, LeadNote, UTMSource
from .forms import LeadForm, LeadNoteForm, UTMSourceForm, WebToLeadForm
from .services import RoundRobinAssigner


def _get_leads_qs(user):
    if user.is_manager:
        return Lead.objects.select_related('assigned_to', 'utm_source').all()
    elif user.is_supervisor:
        team = user.team_members.filter(role=User.EXPERT)
        return Lead.objects.select_related('assigned_to', 'utm_source').filter(assigned_to__in=team)
    return Lead.objects.select_related('assigned_to', 'utm_source').filter(assigned_to=user)


@login_required
def lead_list(request):
    qs = _get_leads_qs(request.user)

    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(phone__icontains=search)

    counts = {
        'total': _get_leads_qs(request.user).count(),
        'new': _get_leads_qs(request.user).filter(status='new').count(),
        'converted': _get_leads_qs(request.user).filter(status='converted').count(),
        'lost': _get_leads_qs(request.user).filter(status='lost').count(),
    }

    return render(request, 'leads/lead_list.html', {
        'leads': qs,
        'counts': counts,
        'status_choices': Lead.STATUS_CHOICES,
        'current_status': status_filter,
        'search': search,
    })


@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(_get_leads_qs(request.user), pk=pk)
    note_form = LeadNoteForm()

    if request.method == 'POST' and 'add_note' in request.POST:
        note_form = LeadNoteForm(request.POST)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.lead = lead
            note.created_by = request.user
            note.save()
            messages.success(request, 'یادداشت ثبت شد.')
            return redirect('leads:detail', pk=pk)

    return render(request, 'leads/lead_detail.html', {
        'lead': lead,
        'note_form': note_form,
        'notes': lead.lead_notes.select_related('created_by').all(),
        'invoices': lead.invoices.all(),
    })


@login_required
def lead_create(request):
    form = LeadForm(request.POST or None, requesting_user=request.user)
    if request.method == 'POST' and form.is_valid():
        lead = form.save(commit=False)
        if request.user.is_expert:
            lead.assigned_to = request.user
        lead.save()
        messages.success(request, f'سرنخ «{lead.name}» ثبت شد.')
        return redirect('leads:detail', pk=lead.pk)
    return render(request, 'leads/lead_form.html', {'form': form, 'action': 'ثبت سرنخ جدید'})


@login_required
def lead_edit(request, pk):
    lead = get_object_or_404(_get_leads_qs(request.user), pk=pk)
    if request.user.is_expert and lead.assigned_to != request.user:
        return HttpResponseForbidden()

    form = LeadForm(request.POST or None, instance=lead, requesting_user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'سرنخ بروزرسانی شد.')
        return redirect('leads:detail', pk=pk)
    return render(request, 'leads/lead_form.html', {'form': form, 'action': 'ویرایش سرنخ', 'lead': lead})


@login_required
def lead_assign(request, pk):
    """تخصیص دستی لید به کارشناس"""
    if request.user.is_expert:
        return HttpResponseForbidden()
    lead = get_object_or_404(_get_leads_qs(request.user), pk=pk)
    expert_id = request.POST.get('expert_id')
    if expert_id:
        expert = get_object_or_404(User, pk=expert_id, role=User.EXPERT)
        lead.assigned_to = expert
        lead.save(update_fields=['assigned_to'])
        messages.success(request, f'سرنخ به «{expert.full_name_or_username}» ارجاع شد.')
    return redirect('leads:detail', pk=pk)


@login_required
def lead_auto_assign(request, pk):
    """تخصیص خودکار Round Robin"""
    if request.user.is_expert:
        return HttpResponseForbidden()
    lead = get_object_or_404(_get_leads_qs(request.user), pk=pk)
    supervisor = request.user if request.user.is_supervisor else None
    expert = RoundRobinAssigner.assign(lead, supervisor=supervisor)
    if expert:
        messages.success(request, f'سرنخ به صورت خودکار به «{expert.full_name_or_username}» تخصیص یافت.')
    else:
        messages.warning(request, 'کارشناس مناسبی با ظرفیت خالی یافت نشد.')
    return redirect('leads:detail', pk=pk)


# ──────────────── Web-to-Lead (UTM Capture) ────────────────

def capture_lead(request, token):
    """Endpoint عمومی ثبت لید از لینک تبلیغاتی"""
    source = get_object_or_404(UTMSource, token=token, is_active=True)

    if request.method == 'POST':
        form = WebToLeadForm(request.POST)
        if form.is_valid():
            lead = Lead.objects.create(
                name=form.cleaned_data['name'],
                phone=form.cleaned_data['phone'],
                email=form.cleaned_data.get('email', ''),
                utm_source=source,
                source_detail=f"{source.utm_source} / {source.utm_medium}",
                status=Lead.NEW,
            )
            RoundRobinAssigner.assign(lead)
            return render(request, 'leads/capture_success.html', {'source': source})
        return render(request, 'leads/capture_form.html', {'form': form, 'source': source})

    form = WebToLeadForm()
    return render(request, 'leads/capture_form.html', {'form': form, 'source': source})


# ──────────────── UTM Source Management ────────────────

@login_required
def utm_list(request):
    if not request.user.is_manager:
        return HttpResponseForbidden()
    sources = UTMSource.objects.all().order_by('-created_at')
    return render(request, 'leads/utm_list.html', {'sources': sources})


@login_required
def utm_create(request):
    if not request.user.is_manager:
        return HttpResponseForbidden()
    form = UTMSourceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        source = form.save()
        messages.success(request, f'کمپین «{source.name}» ایجاد شد.')
        return redirect('leads:utm_list')
    return render(request, 'leads/utm_form.html', {'form': form})
