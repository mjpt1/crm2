import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
application = get_wsgi_application()

# راه‌اندازی خودکار در Vercel — فقط یک بار در هر cold start
if os.environ.get('VERCEL'):
    from pathlib import Path
    _flag = Path('/tmp/.crm_ready')
    if not _flag.exists():
        try:
            from django.core.management import call_command
            call_command('migrate', '--noinput', verbosity=0)
            from accounts.models import User
            if not User.objects.filter(username='admin').exists():
                u = User.objects.create_superuser(
                    'admin', 'admin@crm.local', 'admin1234'
                )
                u.role = 'manager'
                u.first_name = 'مدیر'
                u.last_name = 'سیستم'
                u.save()
            _flag.touch()
        except Exception as exc:
            print(f'[CRM] setup error: {exc}')
