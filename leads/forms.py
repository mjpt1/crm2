from django import forms
from accounts.models import User
from .models import Lead, LeadNote, UTMSource


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['name', 'phone', 'email', 'company', 'source_detail', 'assigned_to', 'status', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'source_detail': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, requesting_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].empty_label = '--- انتخاب کارشناس ---'
        if requesting_user:
            if requesting_user.is_manager:
                self.fields['assigned_to'].queryset = User.objects.filter(
                    role=User.EXPERT, is_active=True
                )
            elif requesting_user.is_supervisor:
                self.fields['assigned_to'].queryset = User.objects.filter(
                    supervisor=requesting_user, role=User.EXPERT, is_active=True
                )
            else:
                self.fields['assigned_to'].queryset = User.objects.filter(pk=requesting_user.pk)
                self.fields['assigned_to'].widget = forms.HiddenInput()


class LeadNoteForm(forms.ModelForm):
    class Meta:
        model = LeadNote
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'یادداشت جدید...',
            })
        }
        labels = {'content': ''}


class UTMSourceForm(forms.ModelForm):
    class Meta:
        model = UTMSource
        fields = ['name', 'utm_source', 'utm_medium', 'utm_campaign', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'utm_source': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'utm_medium': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'utm_campaign': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
        }


class WebToLeadForm(forms.Form):
    """فرم ثبت لید از طریق لینک تبلیغاتی"""
    name = forms.CharField(
        label='نام و نام خانوادگی',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label='شماره تماس',
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'})
    )
    email = forms.EmailField(
        label='ایمیل',
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'dir': 'ltr'})
    )
