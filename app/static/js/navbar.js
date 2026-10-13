/**
 * LostFound - Mobile Navbar Drawer Interactivity
 * Accessible, zero-dependency vanilla JS for mobile menu
 */
document.addEventListener('DOMContentLoaded', function () {
  const toggleBtn = document.getElementById('nav-toggle-btn');
  const toggleCheckbox = document.getElementById('nav-toggle');
  const navMenu = document.getElementById('nav-menu');
  const header = document.querySelector('.lf-header');

  if (!navMenu) return;

  function setOpen(isOpen) {
    if (toggleCheckbox) {
      toggleCheckbox.checked = isOpen;
    }
    if (toggleBtn) {
      toggleBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      toggleBtn.classList.toggle('active', isOpen);
    }
    navMenu.classList.toggle('is-open', isOpen);
    if (header) {
      header.classList.toggle('nav-is-open', isOpen);
    }
  }

  function toggle(e) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    const isCurrentlyOpen = navMenu.classList.contains('is-open') || (toggleCheckbox && toggleCheckbox.checked);
    setOpen(!isCurrentlyOpen);
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', toggle);
    toggleBtn.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggle();
      }
    });
  }

  if (toggleCheckbox) {
    toggleCheckbox.addEventListener('change', function () {
      setOpen(toggleCheckbox.checked);
    });
  }

  // Close when clicking any navigation link inside navMenu
  navMenu.addEventListener('click', function (e) {
    const link = e.target.closest('a, button');
    if (link) {
      setOpen(false);
    }
  });

  // Close when clicking outside header / navMenu
  document.addEventListener('click', function (e) {
    if (header && !header.contains(e.target)) {
      setOpen(false);
    }
  });

  // Close when pressing Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' || e.key === 'Esc') {
      const isCurrentlyOpen = navMenu.classList.contains('is-open') || (toggleCheckbox && toggleCheckbox.checked);
      if (isCurrentlyOpen) {
        setOpen(false);
        if (toggleBtn) toggleBtn.focus();
      }
    }
  });

  // Auto-close menu if resized to desktop (>= 768px)
  window.addEventListener('resize', function () {
    if (window.innerWidth >= 768) {
      setOpen(false);
    }
  });
});
