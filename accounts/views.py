from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden

from .models import User
from .forms import LoginForm, UserCreateForm, UserEditForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get('next', 'dashboard:index'))
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def user_list(request):
    user = request.user
    if user.is_expert:
        return HttpResponseForbidden()

    if user.is_manager:
        supervisors = User.objects.filter(role=User.SUPERVISOR, is_active=True)
        experts = User.objects.filter(role=User.EXPERT, is_active=True)
    else:
        supervisors = User.objects.none()
        experts = User.objects.filter(supervisor=user, role=User.EXPERT, is_active=True)

    return render(request, 'accounts/user_list.html', {
        'supervisors': supervisors,
        'experts': experts,
    })


@login_required
def user_create(request):
    if request.user.is_expert:
        return HttpResponseForbidden()

    form = UserCreateForm(
        request.POST or None,
        requesting_user=request.user
    )
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        if request.user.is_supervisor and user.role == User.EXPERT:
            user.supervisor = request.user
            user.save(update_fields=['supervisor'])
        messages.success(request, f'کاربر «{user.full_name_or_username}» با موفقیت ایجاد شد.')
        return redirect('accounts:user_list')

    return render(request, 'accounts/user_form.html', {'form': form, 'action': 'ایجاد'})


@login_required
def user_edit(request, pk):
    if request.user.is_expert:
        return HttpResponseForbidden()

    target = get_object_or_404(User, pk=pk)

    if request.user.is_supervisor:
        if not (target.supervisor == request.user and target.role == User.EXPERT):
            return HttpResponseForbidden()

    form = UserEditForm(request.POST or None, request.FILES or None, instance=target)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'اطلاعات کاربر بروزرسانی شد.')
        return redirect('accounts:user_list')

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'action': 'ویرایش',
        'target': target,
    })


@login_required
def user_toggle_active(request, pk):
    if not request.user.is_manager:
        return HttpResponseForbidden()
    target = get_object_or_404(User, pk=pk)
    target.is_active = not target.is_active
    target.save(update_fields=['is_active'])
    state = 'فعال' if target.is_active else 'غیرفعال'
    messages.info(request, f'کاربر «{target.full_name_or_username}» {state} شد.')
    return redirect('accounts:user_list')


@login_required
def toggle_online(request):
    """تغییر وضعیت آنلاین/آفلاین کارشناس"""
    user = request.user
    user.is_online = not user.is_online
    user.save(update_fields=['is_online'])
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:index'))


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'target': request.user})
