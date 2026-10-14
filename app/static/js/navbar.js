/**
 * LostFound - Left Sidebar & Responsive Drawer Navigation
 * Accessible, zero-dependency vanilla JS for drawer interactivity and theme toggling
 */
document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.getElementById('lf-sidebar');
  const mobileMenuBtn = document.getElementById('mobile-menu-btn');
  const sidebarCloseBtn = document.getElementById('sidebar-close-btn');
  const backdrop = document.getElementById('lf-sidebar-backdrop');

  function openSidebar() {
    if (sidebar) sidebar.classList.add('is-open');
    if (backdrop) backdrop.classList.add('is-open');
    if (mobileMenuBtn) mobileMenuBtn.setAttribute('aria-expanded', 'true');
    document.body.classList.add('lf-drawer-open');
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('is-open');
    if (backdrop) backdrop.classList.remove('is-open');
    if (mobileMenuBtn) {
      mobileMenuBtn.setAttribute('aria-expanded', 'false');
      try {
        mobileMenuBtn.focus();
      } catch (e) {}
    }
    document.body.classList.remove('lf-drawer-open');
  }

  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      const isOpen = sidebar && sidebar.classList.contains('is-open');
      if (isOpen) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener('click', function (e) {
      e.preventDefault();
      closeSidebar();
    });
  }

  if (backdrop) {
    backdrop.addEventListener('click', function () {
      closeSidebar();
    });
  }

  // Close when pressing Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' || e.key === 'Esc') {
      if (sidebar && sidebar.classList.contains('is-open')) {
        closeSidebar();
      }
    }
  });

  // Close on mobile (< 992px) when clicking any navigation link
  if (sidebar) {
    sidebar.addEventListener('click', function (e) {
      const link = e.target.closest('a');
      if (link && window.innerWidth < 992) {
        closeSidebar();
      }
    });
  }

  // Auto-close drawer if resized to desktop (>= 992px)
  window.addEventListener('resize', function () {
    if (window.innerWidth >= 992 && sidebar && sidebar.classList.contains('is-open')) {
      closeSidebar();
    }
  });

  // Light / Dark Mode Interactive Toggle (Sidebar & Mobile Header)
  const themeBtns = document.querySelectorAll('.lf-theme-toggle');

  function updateThemeButtons(theme) {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    const label = 'Switch to ' + nextTheme.charAt(0).toUpperCase() + nextTheme.slice(1) + ' Mode';
    themeBtns.forEach(function (btn) {
      btn.setAttribute('title', label);
      btn.setAttribute('aria-label', label);
    });
  }

  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  updateThemeButtons(currentTheme);

  themeBtns.forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const curr = document.documentElement.getAttribute('data-theme') || 'light';
      const next = curr === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try {
        localStorage.setItem('lf-theme', next);
      } catch (err) {}
      updateThemeButtons(next);
    });
  });

  // Auto-adapt to OS scheme changes if user hasn't explicitly set a preference
  if (window.matchMedia) {
    try {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
        if (!localStorage.getItem('lf-theme')) {
          const sysTheme = e.matches ? 'dark' : 'light';
          document.documentElement.setAttribute('data-theme', sysTheme);
          updateThemeButtons(sysTheme);
        }
      });
    } catch (err) {}
  }
});
