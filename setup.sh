#!/bin/bash
# ─── اسکریپت راه‌اندازی اولیه سامانه CRM ───

set -e

echo ""
echo "════════════════════════════════════════"
echo "   راه‌اندازی سامانه مدیریت ارتباط با مشتری"
echo "════════════════════════════════════════"
echo ""

# ۱. ایجاد فایل .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ فایل .env ایجاد شد"
    echo "  لطفاً پیش از ادامه مقادیر را ویرایش کنید: nano .env"
    exit 0
fi

# ۲. راه‌اندازی پایگاه داده
echo "▸ راه‌اندازی PostgreSQL..."
docker compose up -d db

echo "▸ انتظار برای آماده شدن پایگاه داده..."
until docker compose exec db pg_isready -q; do sleep 2; done

# ۳. اجرای مایگریشن‌ها
echo "▸ اجرای مایگریشن‌ها..."
docker compose run --rm web python manage.py migrate --noinput

# ۴. جمع‌آوری فایل‌های استاتیک
echo "▸ جمع‌آوری فایل‌های استاتیک..."
docker compose run --rm web python manage.py collectstatic --noinput

# ۵. ایجاد ادمین
echo ""
echo "▸ ایجاد حساب مدیر کل:"
docker compose run --rm web python manage.py createsuperuser

# ۶. راه‌اندازی همه سرویس‌ها
echo ""
echo "▸ راه‌اندازی کامل سامانه..."
docker compose up -d

echo ""
echo "════════════════════════════════════════"
echo "   سامانه با موفقیت راه‌اندازی شد!"
echo "   آدرس: http://localhost"
echo "   پنل مدیریت: http://localhost/admin/"
echo "════════════════════════════════════════"
echo ""
