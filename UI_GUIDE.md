# LostFound Design System & Front-End UI Guide

This guide documents the design system architecture, CSS custom properties (tokens), layout patterns, component specifications, and zero-JavaScript interactive techniques for the **LostFound: Smart Lost & Found Management System**.

---

## 1. Design System Philosophy & Architecture

The LostFound UI is built on a **Zero-JavaScript, Pure CSS3 & HTML5** architecture designed for high performance, universal accessibility, and seamless responsiveness across devices from 320px smartphones to 1920px large desktop displays.

### Core Architecture Principles
1. **Zero Client-Side JavaScript:** Every interactive behavior—including mobile navigation, accordions, tabs, notifications, and modal dialogs—is implemented with declarative HTML5 elements (`<details>`, `<summary>`) and CSS pseudo-classes (`:checked`, `:target`, `:hover`, `:focus-visible`).
2. **Design Tokens First:** All colors, spacing, typography scales, border radii, shadows, and transitions are defined as CSS Custom Properties in `:root`.
3. **Mobile-First Layout:** Default CSS rules target narrow screens (320px+). Progressive enhancement is applied through `min-width` media queries at standardized breakpoints.
4. **Universal Accessibility (WCAG 2.1 AA):** All color pairs guarantee a minimum 4.5:1 contrast ratio. Interactive elements maintain a minimum 44×44px touch hitbox. Focus states are prominent and unambiguous.
5. **Adaptive User Preferences:** Full support for `prefers-color-scheme: dark` (high-contrast dark mode) and `prefers-reduced-motion: reduce` (elimination of non-essential transitions).

---

## 2. Design Tokens (CSS Custom Properties)

All tokens are defined in `app/static/css/style.css` under `:root` and overridden under `@media (prefers-color-scheme: dark)`.

### 2.1 Color Tokens & Contrast Ratios

```css
:root {
  /* Core Brand Colors */
  --color-primary: #1d4ed8;          /* WCAG AA 4.7:1 against light surface */
  --color-primary-dark: #1e40af;
  --color-primary-light: #eff6ff;
  --color-secondary: #475569;
  --color-secondary-light: #f1f5f9;

  /* Surface & Background */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-subtle: #f1f5f9;
  --color-border: #cbd5e1;
  --color-border-subtle: #e2e8f0;

  /* Typography */
  --color-text: #0f172a;             /* High contrast dark slate */
  --color-text-muted: #475569;       /* WCAG AA compliant muted text */
  --color-text-inverse: #ffffff;

  /* Semantic Feedback & Statuses */
  --color-success: #15803d;          /* Approved / Returned / Active Match */
  --color-success-bg: #f0fdf4;
  --color-warning: #b45309;          /* Possible Match / Pending Review */
  --color-warning-bg: #fffbeb;
  --color-danger: #b91c1c;           /* Rejected / Expired */
  --color-danger-bg: #fef2f2;
  --color-info: #0369a1;             /* Reported / Info */
  --color-info-bg: #f0f9ff;
  --color-purple: #6d28d9;           /* Under Review */
  --color-purple-bg: #f5f3ff;
  --color-archive: #64748b;          /* Archived / Inactive */
  --color-archive-bg: #f8fafc;
}
```

#### Status Color Consistency Map
Status badges throughout the application use consistent semantic tokens:
- **Reported:** `--color-info` (#0369a1) + icon
- **Possible Match:** `--color-warning` (#b45309) + icon
- **Under Review:** `--color-purple` (#6d28d9) + icon
- **Approved / Returned / Handed Over:** `--color-success` (#15803d) + icon
- **Rejected:** `--color-danger` (#b91c1c) + icon
- **Archived / Stale:** `--color-archive` (#64748b) + icon

### 2.2 Typography Scale (Fluid with `clamp()`)

Typography employs a modern system font stack with fluid sizing using CSS `clamp()` so titles scale smoothly without abrupt jumps:

```css
:root {
  --font-family-base: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-family-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;

  /* Fluid Scales */
  --font-size-base: 1rem;            /* 16px root baseline */
  --font-size-sm: 0.875rem;          /* 14px */
  --font-size-xs: 0.75rem;           /* 12px */
  --font-size-h4: clamp(1.125rem, 2vw, 1.25rem);
  --font-size-h3: clamp(1.25rem, 2.5vw, 1.5rem);
  --font-size-h2: clamp(1.5rem, 3.2vw, 1.875rem);
  --font-size-h1: clamp(1.75rem, 4vw, 2.375rem);
  --font-size-hero: clamp(2rem, 5vw, 2.875rem);

  --line-height-tight: 1.2;
  --line-height-base: 1.5;
  --line-height-relaxed: 1.625;
}
```

### 2.3 8-Point Spacing Scale

Spacing uses a consistent 8-point geometric scale. Arbitrary margins and paddings are strictly disallowed:

```css
:root {
  --space-1: 0.25rem; /* 4px */
  --space-2: 0.5rem;  /* 8px */
  --space-3: 0.75rem; /* 12px */
  --space-4: 1rem;    /* 16px */
  --space-5: 1.25rem; /* 20px */
  --space-6: 1.5rem;  /* 24px */
  --space-8: 2rem;    /* 32px */
  --space-10: 2.5rem; /* 40px */
  --space-12: 3rem;   /* 48px */
  --space-16: 4rem;   /* 64px */
}
```

### 2.4 Border Radius, Shadows, and Transitions

```css
:root {
  --radius-sm: 0.25rem;  /* 4px */
  --radius-md: 0.375rem; /* 6px */
  --radius-lg: 0.5rem;   /* 8px */
  --radius-xl: 0.75rem;  /* 12px */
  --radius-full: 9999px;

  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);

  --transition-fast: 150ms ease-in-out;
  --transition-base: 200ms ease-in-out;
}
```

---

## 3. Responsive Breakpoints & Viewport Grid

The application uses mobile-first media queries (`min-width`) conforming to standard hardware device boundaries:

| Breakpoint Name | Media Query | Target Hardware Devices |
|---|---|---|
| **xs** (Mobile base) | `< 576px` | 320px (SE), 375px (iPhone), 414px (Plus/Max) |
| **sm** | `@media (min-width: 576px)` | Large phones landscape, small phablets |
| **md** | `@media (min-width: 768px)` | Tablets portrait (iPad), small netbooks |
| **lg** | `@media (min-width: 992px)` | Tablets landscape, ultra-portables |
| **xl** | `@media (min-width: 1200px)` | Laptops, standard desktop displays |
| **xxl** | `@media (min-width: 1400px)` | Widescreen monitors (1440px, 1920px) |

### Max-Width Containers & Padding
Page content is centered inside containers with fluid side margins:
```css
.container {
  width: 100%;
  max-width: 1280px;
  margin-left: auto;
  margin-right: auto;
  padding-left: var(--space-4);  /* 16px on mobile */
  padding-right: var(--space-4);
}
@media (min-width: 768px) {
  .container {
    padding-left: var(--space-6); /* 24px on tablet */
    padding-right: var(--space-6);
  }
}
@media (min-width: 1200px) {
  .container {
    padding-left: var(--space-8); /* 32px on desktop */
    padding-right: var(--space-8);
  }
}
```

---

## 4. Zero-JavaScript Interactive Patterns

### 4.1 Responsive Role-Based Navigation (1 Clickable Button Per Page)
The application employs a strictly unified, role-based navigation model where **every destination page has exactly one clickable button** with a visible icon and text label. On mobile (<992px), navigation collapses cleanly into a hamburger icon powered entirely by a native checkbox and CSS pseudo-class:

```html
<header class="lf-header" role="banner">
  <div class="lf-nav-container">
    <a href="/" class="lf-brand" aria-label="LostFound Home">
      <i class="bi bi-compass-fill me-2" aria-hidden="true"></i>
      <span>Lost<span class="text-primary">Found</span></span>
    </a>

    <!-- Pure CSS Toggle Checkbox & Accessible Label -->
    <input type="checkbox" id="nav-toggle" class="lf-nav-toggle-input" aria-label="Toggle navigation menu">
    <label for="nav-toggle" class="lf-nav-toggle-label" tabindex="0" role="button" aria-controls="nav-menu" aria-label="Toggle navigation menu">
      <i class="bi bi-list" aria-hidden="true"></i>
    </label>

    <!-- Navigation Content: 1 Clickable Button Per Page -->
    <div id="nav-menu" class="lf-nav-content">
      <nav class="lf-nav-links" aria-label="Main Navigation">
        <!-- Core Links (Public / User) -->
        <a href="/auth/dashboard" class="lf-nav-btn active" aria-current="page"><i class="bi bi-speedometer2 text-primary me-1"></i>Dashboard</a>
        <a href="/lost" class="lf-nav-btn"><i class="bi bi-search text-danger me-1"></i>Lost Reports</a>
        <a href="/found" class="lf-nav-btn"><i class="bi bi-box-seam text-success me-1"></i>Found Items</a>
        <a href="/claims/my" class="lf-nav-btn"><i class="bi bi-file-earmark-check text-success me-1"></i>My Claims</a>
        <a href="/views/map" class="lf-nav-btn"><i class="bi bi-geo-alt text-primary me-1"></i>Map</a>
        <a href="/views/calendar" class="lf-nav-btn"><i class="bi bi-calendar3 text-primary me-1"></i>Calendar</a>

        <!-- Staff Operational Buttons -->
        <a href="/kanban" class="lf-nav-btn"><i class="bi bi-kanban text-primary me-1"></i>Kanban</a>
        <a href="/claims/queue" class="lf-nav-btn"><i class="bi bi-check2-square text-info me-1"></i>Review Claims</a>
        <a href="/reports" class="lf-nav-btn"><i class="bi bi-bar-chart text-dark me-1"></i>Reports</a>

        <!-- Admin Management Buttons -->
        <a href="/admin/categories" class="lf-nav-btn"><i class="bi bi-tags text-primary me-1"></i>Categories</a>
        <a href="/admin/locations" class="lf-nav-btn"><i class="bi bi-pin-map text-primary me-1"></i>Locations</a>
        <a href="/admin/settings" class="lf-nav-btn"><i class="bi bi-gear text-secondary me-1"></i>Settings</a>
        <a href="/admin/users" class="lf-nav-btn"><i class="bi bi-people text-info me-1"></i>Users</a>
        <a href="/admin/archive" class="lf-nav-btn"><i class="bi bi-archive text-warning me-1"></i>Archive</a>
        <a href="/admin/audit" class="lf-nav-btn"><i class="bi bi-journal-text text-dark me-1"></i>Audit Log</a>
      </nav>

      <!-- Account Controls: 1 Button for Profile, 1 Button for Sign Out -->
      <div class="lf-nav-auth" aria-label="User Navigation">
        <a href="/auth/profile" class="lf-nav-btn"><i class="bi bi-person-circle text-secondary me-1"></i>Profile</a>
        <form action="/auth/logout" method="POST" class="d-inline m-0 p-0">
          <input type="hidden" name="csrf_token" value="...">
          <button type="submit" class="lf-nav-btn lf-nav-btn-logout"><i class="bi bi-box-arrow-right text-danger me-1"></i>Sign Out</button>
        </form>
      </div>
    </div>
  </div>
</header>
```

```css
/* Responsive Nav Behavior in CSS */
.lf-nav-toggle-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}
@media (max-width: 991.98px) {
  .lf-nav-toggle-label {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    cursor: pointer;
  }
  .lf-nav-content {
    display: none;
    width: 100%;
    flex-direction: column;
    padding: 0.75rem 0 1rem;
    border-top: 1px solid var(--lf-border);
  }
  .lf-nav-toggle-input:checked ~ .lf-nav-content {
    display: flex;
  }
  .lf-nav-btn {
    width: 100%;
    min-height: 44px;
    padding: 0.6rem 0.85rem;
    font-size: 0.95rem;
    justify-content: flex-start;
  }
}
@media (min-width: 992px) {
  .lf-nav-toggle-label {
    display: none;
  }
  .lf-nav-content {
    display: flex !important;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    flex: 1;
  }
  .lf-nav-btn {
    width: auto;
    padding: 0.35rem 0.6rem;
    min-height: 38px;
    font-size: 0.825rem;
  }
}
```

### 4.2 Collapsible Filter Panels (`<details>` / `<summary>`)
Catalog filters collapse on mobile devices to preserve vertical screen estate:

```html
<details class="filter-details" open>
  <summary class="filter-summary">
    <span class="filter-summary-title">Filter & Search</span>
    <span class="filter-summary-icon">▾</span>
  </summary>
  <form method="GET" class="filter-form-grid">
    <!-- Filter fields -->
  </form>
</details>
```

```css
@media (max-width: 991.98px) {
  .filter-details:not([open]) .filter-form-grid {
    display: none;
  }
  .filter-summary {
    display: flex;
    justify-content: space-between;
    min-height: 44px;
    align-items: center;
    cursor: pointer;
  }
}
```

### 4.3 Pure CSS Modal Confirmation (`:target` Dialog)
Destructive actions (e.g. Purging Archive) use CSS `:target` modals instead of JavaScript `alert()` or `confirm()`:

```html
<!-- Trigger link -->
<a href="#confirm-purge-modal" class="btn btn-danger">Purge Expired Records</a>

<!-- Pure CSS Modal Dialog -->
<div id="confirm-purge-modal" class="lf-modal-backdrop">
  <div class="lf-modal-dialog">
    <h3>Confirm Permanent Deletion</h3>
    <p>Are you sure you want to permanently purge all expired items? This action cannot be undone.</p>
    <div class="lf-modal-actions">
      <a href="#" class="btn btn-secondary">Cancel</a>
      <form method="POST" action="/admin/archive/purge">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <button type="submit" class="btn btn-danger">Confirm Purge</button>
      </form>
    </div>
  </div>
</div>
```

```css
.lf-modal-backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  z-index: 1050;
  align-items: center;
  justify-content: center;
}
.lf-modal-backdrop:target {
  display: flex;
}
```

---

## 5. Component Specifications

### 5.1 Buttons
- **Touch Target:** Minimum height and width `44px` with `display: inline-flex; align-items: center; justify-content: center;`.
- **Variants:**
  - `.btn-primary`: Solid blue (`--color-primary`), white text.
  - `.btn-secondary`: Neutral slate (`--color-secondary`), white text.
  - `.btn-success`: Forest green (`--color-success`), white text.
  - `.btn-danger`: Crimson red (`--color-danger`), white text.
  - `.btn-outline`: Transparent surface with `--color-border` stroke.

### 5.2 Responsive Tables & Card Stacking
To support dense data on phones without clipping:
- Wrap in `.table-container` for desktop horizontal containment (`overflow-x: auto;`).
- Add `.responsive-table` and `data-label="..."` on every `<td>`:

```css
@media (max-width: 767.98px) {
  .responsive-table thead {
    display: none;
  }
  .responsive-table tr {
    display: block;
    margin-bottom: var(--space-4);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-3);
  }
  .responsive-table td {
    display: flex;
    justify-content: space-between;
    padding: var(--space-2) 0;
    border-bottom: 1px solid var(--color-border-subtle);
  }
  .responsive-table td::before {
    content: attr(data-label);
    font-weight: 600;
    color: var(--color-text-muted);
  }
}
```

### 5.3 Kanban Board (Scroll Snap)
The 5-stage workflow board supports touch gestures:
- On screens `< 1200px`: uses `display: flex; overflow-x: auto; scroll-snap-type: x mandatory; gap: 1rem;`. Each column is sized to `85vw` on phones and `320px` on tablets.
- On screens `≥ 1200px`: uses `display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem;`.
- Column headers are `position: sticky; top: 0;` to keep counts and labels visible.

### 5.4 Calendar (Dual-Mode: 7-Col Desktop vs Mobile Agenda)
- On desktop (`≥ 768px`): Displays full 7-day grid (`grid-template-columns: repeat(7, 1fr)`) with event count indicators and active day borders.
- On phones (`< 768px`): Automatically transforms via CSS into an **Agenda List layout** displaying days with active events, preventing 38px column squishing.

### 5.5 Map View (Folium Responsive Embed)
- Container height uses fluid clamp: `height: clamp(320px, 60vh, 720px); width: 100%; border-radius: var(--radius-lg); overflow: hidden;`.
- Sidebar filters stack above map on mobile and dock alongside on desktop (`grid-template-columns: 320px 1fr`).

---

## 6. Accessibility & Print Standards

### 6.1 WCAG 2.1 AA Compliance Checklist
- [x] **Focus Indicator:** All interactive elements feature `:focus-visible { outline: 3px solid var(--color-primary); outline-offset: 2px; }`.
- [x] **Skip Link:** Dedicated `<a href="#main-content" class="skip-link">Skip to main content</a>` rendered as the first element in `base.html`.
- [x] **Visual Status Badges:** Badges combine icons + descriptive text (never relying on color alone).
- [x] **Form Inputs:** Linked `<label for="id">`, visible validation error hints, and explicit `autocomplete` tokens.

### 6.2 Print Stylesheet (`@media print`)
When printing claim receipts or handover documentation:
```css
@media print {
  .lf-navbar,
  .lf-footer,
  .btn,
  .filter-details,
  .skip-link {
    display: none !important;
  }
  body {
    background: #ffffff !important;
    color: #000000 !important;
    font-size: 12pt;
  }
  .card, .table-container {
    border: 1px solid #cccccc !important;
    box-shadow: none !important;
    page-break-inside: avoid;
  }
}
```

---

## 7. Maintenance & Extension Rules

When adding new screens or modifying existing templates:
1. **Never inject JavaScript:** Do not use `<script>` tags, CDN script bundles, or inline `onclick`/`onsubmit` handlers.
2. **Preserve Design Tokens:** Always use `var(--color-*)`, `var(--space-*)`, and `var(--radius-*)` instead of hardcoded hex or pixel values.
3. **Always Add `data-label` on Tables:** When building `<table>` templates, always annotate every `<td>` with `data-label="Column Name"` so mobile card-stacking functions automatically.
4. **Enforce Touch Target Minimums:** Ensure every interactive button or link has at least `44px` height and adequate margin.
5. **Verify Zero Horizontal Scroll:** Test changes at 320px, 375px, and 1440px to confirm `document.documentElement.scrollWidth === document.documentElement.clientWidth`.
