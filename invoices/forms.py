from django import forms
from .models import Invoice
from leads.models import Lead
from accounts.models import User


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['lead', 'amount', 'description']
        widgets = {
            'lead': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'lead': 'سرنخ / مشتری',
            'amount': 'مبلغ (تومان)',
            'description': 'شرح خدمات',
        }

    def __init__(self, *args, requesting_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if requesting_user:
            if requesting_user.is_expert:
                self.fields['lead'].queryset = Lead.objects.filter(
                    assigned_to=requesting_user
                ).exclude(status='lost')
            elif requesting_user.is_supervisor:
                team = requesting_user.team_members.filter(role=User.EXPERT)
                self.fields['lead'].queryset = Lead.objects.filter(
                    assigned_to__in=team
                ).exclude(status='lost')
            else:
                self.fields['lead'].queryset = Lead.objects.exclude(status='lost')
        self.fields['lead'].empty_label = '--- انتخاب سرنخ ---'
