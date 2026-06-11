#!/usr/bin/env bash
set -e
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py shell -c "
from accounts.models import User
if not User.objects.filter(username='admin').exists():
    u = User.objects.create_superuser('admin', 'admin@crm.local', 'admin1234')
    u.role = 'manager'
    u.first_name = 'مدیر'
    u.last_name = 'سیستم'
    u.save()
    print('superuser created')
"
