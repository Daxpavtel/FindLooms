# LostFound Campus — Technical Architecture & Stack Specification

## 1. System Overview

**LostFound Campus** is an enterprise-grade, institutional Lost & Found lifecycle management platform built for universities, schools, and corporate campuses. The system is designed with a **Server-Side Rendered (SSR), Zero-Heavy-JS** philosophy, ensuring instant page loads, robust accessibility (WCAG 2.1 AA), end-to-end data privacy, and verifiable chain-of-custody tracking.

---

## 2. Architecture Breakdown

```
+-----------------------------------------------------------------------------------+
|                                  CLIENT LAYER                                     |
|  - Modern Browsers (Desktop, Tablet, Mobile 375px - 1440px+)                      |
|  - Bootstrap 5.3 CSS-only + Bootstrap Icons 1.11.3 (Zero JS Frameworks)          |
|  - Custom CSS Design System with CSS Tokens (--lf-surface, --lf-text, etc.)       |
|  - Lightweight Vanilla JS: 3-line sliding navigation drawer & instant theme switch|
+-----------------------------------------------------------------------------------+
                                         │
                                   HTTP / HTTPS
                                         │
+-----------------------------------------------------------------------------------+
|                             APPLICATION TIER (Flask)                              |
|  - WSGI Server: Flask 3.0+ / Werkzeug                                            |
|  - Template Engine: Jinja2 with SSR caching & custom filters                      |
|  - Security & CSRF: Flask-WTF + WTForms + email-validator                         |
|  - Authentication: Flask-Login (Secure Session Cookies, HttpOnly, SameSite)       |
|  - Role-Based Access Control: 3 Tiers (Student / User, Staff Custodian, Admin)    |
|  - Intelligent Matching Engine: Scikit-learn TF-IDF + Weighted Scoring Matrix     |
|  - Asynchronous Tasks: APScheduler (Automated 30-day retention & archival)        |
+-----------------------------------------------------------------------------------+
                                         │
                                  PyMongo 4.6+
                                         │
+-----------------------------------------------------------------------------------+
|                               DATA TIER (MongoDB)                                 |
|  - Database: MongoDB 6.x / 7.x (or Mongomock for CI/CD)                           |
|  - Collections: users, lost_items, found_items, match_candidates, claims,         |
|                 handovers, audit_logs, categories, locations, counters,           |
|                 item_images, system_settings                                      |
|  - Atomic Counter Sequences: LST-YYYY-XXXX, FND-YYYY-XXXX, CLM-YYYY-XXXX           |
|  - Compound Indexes: reference_no, status, user_id, timestamp, text search        |
+-----------------------------------------------------------------------------------+
```

---

## 3. Technology Stack Matrix

| Tier | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Runtime** | Python | `3.12+` / `3.14` | High-performance core application runtime |
| **Web Framework** | Flask | `^3.0.0` | Lightweight, scalable microframework routing & context handling |
| **Authentication** | Flask-Login | `^0.6.3` | User session management, secure cookie handling |
| **Form & Validation** | Flask-WTF / WTForms | `^1.2.1` / `^3.1.2` | CSRF protection, input sanitization, form validation |
| **Database Driver** | PyMongo | `^4.6.0` | High-throughput asynchronous-ready MongoDB driver |
| **Database** | MongoDB | `6.0+` / `7.0+` | Flexible JSON document store with indexed queries |
| **Machine Learning / NLP** | Scikit-Learn | `^1.4.0` | TF-IDF text vectorization & cosine similarity for item matching |
| **Image Engine** | Pillow (PIL) | `^10.2.0` | Server-side image sanitization, format conversion, thumbnailing |
| **Task Scheduler** | APScheduler | `^3.10.4` | Background execution of retention policies & recurring jobs |
| **Charting & Analytics** | Matplotlib | `^3.8.0` | Generation of custody reports & statistical aggregations |
| **CSS Framework** | Bootstrap 5.3 (CSS) | `5.3.3` | Production grid, typography, and accessibility utilities |
| **Icons** | Bootstrap Icons | `1.11.3` | Scalable vector icons for high DPI and dark mode |
| **Test Automation** | Pytest / Mongomock | `^8.0.0` / `^4.1.2` | Automated unit, integration, and security regression testing |

---

## 4. Security & Privacy Architecture

### 4.1 Role-Based Access Control (RBAC) Matrix

| Resource / Action | Student / User | Staff Custodian | System Administrator |
| :--- | :---: | :---: | :---: |
| **Browse Public Items** | ✅ | ✅ | ✅ |
| **File Lost Report** | ✅ | ✅ | ✅ |
| **File Ownership Claim** | ✅ | ✅ | ✅ |
| **Register Discovered Item** | ❌ | ✅ | ✅ |
| **Kanban Custody Board** | ❌ | ✅ | ✅ |
| **Review Queue & Claim Approval** | ❌ | ✅ | ✅ |
| **Physical Handover Execution** | ❌ | ✅ | ✅ |
| **Custody Reports** | ❌ | ✅ | ✅ |
| **Immutable Audit Trail** | ❌ | ✅ (`@staff_required`) | ✅ |
| **Manage Users & Role Assignment** | ❌ | ❌ | ✅ (`@admin_required`) |
| **Manage Categories & Locations** | ❌ | ❌ | ✅ (`@admin_required`) |
| **System Settings & Retention Archival** | ❌ | ❌ | ✅ (`@admin_required`) |

### 4.2 Zero-Leakage Privacy Guard
- **Confidential Verification Clues**: Stored in a protected database field (`private_verification_detail`).
- **Data Redaction**: Automatically stripped from all public list, search, and detail endpoints.
- **Access Rule**: Only the original reporter and authorized staff custodians during handover verification can access the private clue.

### 4.3 Defense-in-Depth Protections
- **CSRF Tokens**: Form-level and AJAX-level cryptographic tokens generated per session.
- **IDOR Protection**: Object ownership checks prevent users from altering or reviewing other users' claims by manipulating URL IDs.
- **Password Security**: Werkzeug salted PBKDF2 with SHA-256 (minimum 600,000 iterations).

---

## 5. Intelligent Multi-Criteria Matching Engine

When an item is reported lost or registered as found, the **Matching Service** (`app/services/matching.py`) evaluates candidate compatibility using a weighted 100-point scoring algorithm:

$$\text{Total Score} = S_{\text{cat}} + S_{\text{loc}} + S_{\text{text}} + S_{\text{date}} + S_{\text{color}} + S_{\text{brand}}$$

1. **Category Match (30 pts)**: Strict category code equality check.
2. **Text Description Similarity (25 pts)**: TF-IDF vectorization with n-gram extraction (1-2 words) and cosine distance calculation via Scikit-Learn.
3. **Location Proximity (20 pts)**:
   - Same venue / room: 20 pts
   - Same building / zone: 15 pts
   - Campus general match: 5 pts
4. **Temporal Proximity (15 pts)**: Inverse time distance decay (items within 24–48 hours receive highest score).
5. **Brand & Color Equality (10 pts)**: Exact token intersection checks.

**Automated State Progression**:
- Scores **$\ge 60\%$**: Flagged as *Possible Match*.
- Scores **$\ge 80\%$**: Auto-promoted to *Strong Match* with staff notification.

---

## 6. Frontend Design System

- **Zero Heavy JS Frameworks**: No React, Vue, or Angular bundle overhead. Instant page execution.
- **3-Line Sliding Navigation Bar**: Accessible offcanvas drawer (`#lf-sidebar`) triggered by a prominent 3-line hamburger button on all screen sizes, supporting full keyboard navigation (`Esc`), backdrop dismiss, and link auto-close.
- **CSS Custom Properties Design Tokens**: Instant light/dark mode switching via `data-theme="dark"` / `data-theme="light"` without Flash of Unstyled Content (FOUC).
- **Accessibility & Contrast**: Meets WCAG 2.1 AA standards (minimum 4.5:1 text-to-background contrast ratio across all badges, tables, and cards).
