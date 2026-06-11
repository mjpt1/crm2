/* CRM — اسکریپت‌های عمومی */

document.addEventListener('DOMContentLoaded', () => {
  // ─── Sidebar toggle برای موبایل ───
  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar   = document.getElementById('sidebar');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }

  // ─── Auto-dismiss alerts after 5 seconds ───
  document.querySelectorAll('.alert.alert-dismissible').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // ─── تأیید هنگام خروج از فرم‌های ویرایش ───
  const forms = document.querySelectorAll('form[data-confirm-leave]');
  forms.forEach(form => {
    let changed = false;
    form.querySelectorAll('input, select, textarea').forEach(el => {
      el.addEventListener('change', () => { changed = true; });
    });
    form.addEventListener('submit', () => { changed = false; });
    window.addEventListener('beforeunload', (e) => {
      if (changed) {
        e.preventDefault();
        e.returnValue = 'تغییرات ذخیره نشده از بین می‌روند. آیا مطمئنید؟';
      }
    });
  });

  // ─── کپی لینک ───
  document.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', () => {
      const text = btn.getAttribute('data-copy');
      navigator.clipboard.writeText(text).then(() => {
        const orig = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-check"></i>';
        setTimeout(() => { btn.innerHTML = orig; }, 1500);
      });
    });
  });
});
