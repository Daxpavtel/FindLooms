# LostFound: The Smart Lost & Found Management System

> **A centralized, secure, workflow-driven and traceable Lost & Found platform for university campuses, corporate offices, airports, and event venues.**

Built strictly following a **Zero-JavaScript, pure server-rendered architecture** with Python 3.12, Flask, MongoDB (PyMongo), Scikit-Learn TF-IDF matching, and responsive HTML5/CSS3.

---

## 📑 Table of Contents
1. [Key Features & Highlights](#-key-features--highlights)
2. [Zero-JavaScript Architecture](#-zero-javascript-architecture)
3. [Technology Stack](#-technology-stack)
4. [Prerequisites & Quickstart](#-prerequisites--quickstart)
5. [Demo User Accounts](#-demo-user-accounts)
6. [Core Workflows & User Journeys](#-core-workflows--user-journeys)
7. [Smart Matching Engine Breakdown](#-smart-matching-engine-breakdown)
8. [Database Architecture & Collections](#-database-architecture--collections)
9. [Security & Privacy Guarantees](#-security--privacy-guarantees)
10. [Automated Test Suite](#-automated-test-suite)
11. [Future Enhancements](#-future-enhancements)

---

## 🌟 Key Features & Highlights

- **Role-Based Access Control (RBAC):** Three distinct personas (`User`, `Staff`, `Admin`) with fine-grained access control decorators (`@role_required`, `@staff_required`, `@admin_required`).
- **Explainable Multi-Factor Matching Engine:** Scikit-Learn TF-IDF text similarity combined with categorical, location, color, brand, and temporal heuristics (0–100 score with detailed point breakdown).
- **Zero-Leakage Privacy Protection:** Private verification clues (serial numbers, engravings, phone wallpapers, internal contents) are strictly excluded from public queries and templates; only authenticated staff reviewing claims or custodians can inspect them.
- **Side-by-Side Claim Verification:** Dual-pane comparison screen allowing staff to cross-examine claimant answers directly against the finder's private custody clues before approving or rejecting.
- **CSS-Only Kanban Board:** 5-column stage management board (`Reported`, `Possible Match`, `Claimed`, `Handed Over`, `Closed`) utilizing server-rendered HTML forms and pure CSS swimlanes—no client-side JavaScript required.
- **Server-Rendered Interactive Map & Calendar:** Campus spatial distribution rendered via Folium map embedding and month calendar grid rendered with Python `calendar` module and CSS flexbox.
- **Visual Analytics:** Aggregation pipeline KPI dashboard with server-generated Matplotlib base64 charts and CSV export.
- **Daily Retention & Auto-Archiving:** APScheduler background worker that automatically flags items exceeding retention policies (e.g. 30 days) and enables staff bulk disposal actions.
- **Audit Trail & Event Hooks:** Immutable audit logging for all status transitions, staff logins, claim decisions, and handovers.

---

## 🚫 Zero-JavaScript Architecture

This application was engineered with a **strict Zero-JavaScript constraint**:
- **0 `<script>` tags** anywhere in the Jinja2 template tree.
- **0 `.js` files** in static assets or scripts.
- **0 inline JavaScript event handlers** (`onclick`, `onload`, `javascript:` URLs).

### How Zero-JS Functionality is Achieved:
| Feature | Traditional JS Approach | Our Pure Server-Side Approach |
| :--- | :--- | :--- |
| **Kanban Transitions** | Drag & drop via JS API | Server-side POST forms styled with CSS button icons |
| **Modal / Dialogs** | Bootstrap JS modals | Dedicated, lightweight server-rendered review routes |
| **Map View** | Leaflet / Google Maps JS | Python `folium` generating standalone HTML map embedded via `<iframe>` |
| **Calendar Grid** | FullCalendar.js | Python `calendar.monthcalendar()` rendered into semantic HTML table with badge links |
| **Charts & Graphs** | Chart.js / D3.js | Python `matplotlib` headless backend rendering directly to base64 SVG/PNG data URIs |
| **Search & Filtering** | Debounced AJAX | Clean semantic GET forms with query parameters and pagination |

---

## 🛠 Technology Stack

- **Backend / Web Framework:** Python 3.12+, Flask (Application Factory pattern, Blueprints)
- **Database:** MongoDB 7.0+ (PyMongo driver, atomic counters, compound indexes, aggregation pipelines)
- **Authentication & Sessions:** Flask-Login with secure HTTPOnly cookies and Werkzeug password hashing
- **Form Handling & CSRF:** Flask-WTF with CSRF token validation on all mutating POST requests
- **Matching & NLP:** `scikit-learn` (TF-IDF vectorizer, cosine similarity)
- **Mapping & Spatial:** `folium`
- **Visualization:** `matplotlib` (Agg headless backend)
- **Image Processing:** `Pillow` (PIL) for image upload validation, re-encoding, and thumbnail resizing
- **Background Scheduler:** `APScheduler` (BackgroundScheduler)
- **Testing:** `pytest`, `mongomock`, `requests`

---

## 🚀 Prerequisites & Quickstart

### Prerequisites
- Python 3.11 or 3.12
- MongoDB running locally (default: `mongodb://127.0.0.1:27017`) **OR** a MongoDB Atlas cluster URI.

### 1. Clone & Set Up Virtual Environment

```bash
cd FindLooms
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create or update `.env` in the project root:

```ini
# Environment settings
SECRET_KEY=lostfound-production-super-secret-key-2026
MONGO_URI=mongodb://127.0.0.1:27017/lostfound_db
PORT=5000
UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=5242880
RETENTION_DAYS_DEFAULT=30
STRONG_MATCH_THRESHOLD_DEFAULT=60
DUPLICATE_WINDOW_DAYS_DEFAULT=2
```

> **Using MongoDB Atlas?** Simply set `MONGO_URI` to your Atlas connection string:
> `MONGO_URI=mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/lostfound_db?retryWrites=true&w=majority`

### 4. Seed the Database

Run the idempotent database seed script to populate demo users, categories, campus locations, sample items, claims, and audit logs:

```bash
python seed.py
```

### 5. Run the Application

```bash
python run.py
```

Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 👥 Demo User Accounts

All seed passwords are formatted with a consistent convention:

| Role | Name | Email | Password | Access Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | Rajesh Sharma | `admin@campus.edu` | `AdminPass123!` | System settings, retention policies, audit logs, categories, locations |
| **Staff** | Priya Sharma | `priya.sharma@campus.edu` | `StaffPass123!` | Kanban board, intake found items, review claims, physical handover, reports |
| **Staff** | Vikram Malhotra | `vikram.malhotra@campus.edu` | `StaffPass123!` | Custody management, match resolution, handover appointments |
| **User** | Aarav Patel | `aarav.patel@campus.edu` | `UserPass123!` | Report lost items, search found items, file claims, view claim history |
| **User** | Rohan Verma | `rohan.verma@campus.edu` | `UserPass123!` | Report lost items, track status, view match candidates |
| **User** | Ananya Iyer | `ananya.iyer@campus.edu` | `UserPass123!` | Student user with sample reports |

---

## 🔄 Core Workflows & User Journeys

### Journey 1: User Reports Lost Item
1. User logs in (`aarav.patel@campus.edu`).
2. Navigates to **Report Lost** (`/lost/new`).
3. Inputs item title, category, location, date, description, and **Secret Verification Clue** (e.g. *"Serial ends in X789, Yosemite wallpaper"*).
4. System automatically runs duplicate check. If clear, item is assigned a human-readable atomic sequential reference (`LST-2026-0001`).
5. Matching engine executes in real-time, displaying high-probability candidate matches on the item detail view.

### Journey 2: Staff Registers Found Item
1. Staff member logs in (`priya.sharma@campus.edu`).
2. Navigates to **Register Found** (`/found/new`).
3. Fills in discovered location, custody locker, finder info, public description, and **Private Inspection Detail** (e.g. *"Engraved initials on clasp"*).
4. System flags any potential duplicates found within the last 2 days.
5. Item is created with sequential reference (`FND-2026-0001`) in `Unmatched` status.

### Journey 3: Intelligent Matching & Promotion
1. Matching service calculates similarity scores between new items and active opposites.
2. If score ≥ 60 (configurable threshold), candidate match is saved and items transition to `Possible Match`.
3. "Possible Matches" smart badges appear on cards with explainable score breakdowns.

### Journey 4: Claim Verification & Custody Handover
1. Claimant visits item detail and clicks **File Ownership Claim** (`/claims/new/<found_id>`).
2. Claimant provides security proof answers (e.g. lockscreen pattern or hidden contents). Max 3 claims per user per found item.
3. Staff opens **Claims Queue** (`/claims`) and clicks **Review Claim**.
4. Staff inspects dual-column screen:
   - **Left:** Claimant's submitted proof and lost report details.
   - **Right:** Confidential finder notes and custody storage locker.
5. Staff clicks **Approve Claim**. Claim status transitions to `Approved`, Found item to `Claimed`.
6. Staff schedules or records physical handover (`/claims/<id>/handover`). System records receiver identity and marks claim and found item as `Returned`.

### Journey 5: Kanban Board Stage Management
1. Staff navigates to `/kanban`.
2. Inspects items distributed across 5 swimlanes:
   - *Reported / Unmatched*
   - *Possible Match*
   - *Under Review / Claimed*
   - *Handed Over / Returned*
   - *Closed / Archived*
3. Move items to adjacent stages with one-click server-side transition buttons.

---

## 🧠 Smart Matching Engine Breakdown

The system implements a transparent 100-point multi-factor heuristic engine (`app/services/matching.py`):

$$\text{Total Score} = \text{Category} (30) + \text{Text Similarity} (25) + \text{Location} (20) + \text{Color} (10) + \text{Brand} (10) + \text{Time Decay} (5)$$

- **Category Match (30 pts):** Exact ObjectId match earns full 30 points. Mismatch yields 0 points.
- **TF-IDF Text Similarity (25 pts):** Titles and descriptions are vectorized using Scikit-Learn `TfidfVectorizer` (English stop-words removed, sublinear TF scaling). Cosine similarity score $[0.0, 1.0] \times 25$.
- **Location Proximity (20 pts):**
  - Same specific location ID: **20 pts**
  - Same building or zone: **12 pts**
  - Different zones: **0 pts**
- **Color Match (10 pts):** Normalized color keyword intersection: **10 pts**.
- **Brand Match (10 pts):** Normalized brand string match: **10 pts**.
- **Temporal Proximity (5 pts):**
  - Item found on or after lost date (within 7 days): **5 pts**
  - Item found within 14 days: **3 pts**
  - Item found *before* reported lost date: penalized (-15 pts).

Each candidate match displays an **Explainable Score Breakdown** in the UI:
> *Category: 30/30 | Text TF-IDF: 21/25 | Location (Main Library): 20/20 | Color (Space Grey): 10/10 | Brand (Apple): 10/10 | Date Proximity: 5/5 → **Total Score: 96/100***

---

## 🗄 Database Architecture & Collections

MongoDB database (`lostfound_db`) with PyMongo repository patterns:

| Collection | Key Attributes | Indexes & Constraints |
| :--- | :--- | :--- |
| `users` | `name`, `email`, `password_hash`, `role`, `department`, `phone`, `is_active` | Unique index on `email` |
| `categories` | `name`, `icon`, `description`, `is_active` | Unique index on `name` |
| `locations` | `name`, `building`, `zone`, `latitude`, `longitude`, `is_active` | Unique index on `name` |
| `lost_items` | `reference_no`, `reporter_id`, `name`, `category_id`, `color`, `brand`, `lost_date`, `last_seen_location_id`, `description`, `private_verification_detail`, `stage` | Unique on `reference_no`; compound on `(category_id, stage)` |
| `found_items` | `reference_no`, `finder_id`, `name`, `category_id`, `color`, `brand`, `found_datetime`, `found_location_id`, `custody_location`, `custodian_id`, `private_details`, `status`, `archive_eligible` | Unique on `reference_no`; compound on `(category_id, status)` |
| `match_candidates`| `lost_id`, `found_id`, `score`, `score_breakdown`, `status`, `reviewed_by` | Compound unique on `(lost_id, found_id)` |
| `claims` | `reference_no`, `claimant_id`, `found_id`, `lost_id`, `proof_answer`, `claim_type`, `reviewer_id`, `reviewer_notes`, `status` | Unique on `reference_no`; index on `(claimant_id, found_id)` |
| `handovers` | `claim_id`, `receiver_name`, `reviewer_id`, `scheduled_datetime`, `return_datetime`, `acknowledgement_note` | Unique index on `claim_id` |
| `audit_logs` | `action`, `entity_type`, `entity_id`, `actor_id`, `details`, `timestamp` | Index on `timestamp` (descending) |
| `counters` | `_id` (prefix e.g. `LST`, `FND`), `seq` | Atomic `$inc` via `find_one_and_update` |
| `system_settings`| `key`, `value`, `updated_at` | Unique on `key` |

---

## 🔒 Security & Privacy Guarantees

1. **NoSQL Injection Immunity:** Every single user-provided string ID is sanitized through `app.db.to_object_id()`, validating exact 24-character hexadecimal regex pattern before casting to BSON `ObjectId`. Non-string objects or dict payloads are rejected.
2. **Hidden Detail Projections:** PyMongo queries for public item detail views strictly exclude `private_details` and `private_verification_detail` using MongoDB field projections (`{"private_details": 0}`).
3. **CSRF Protection:** Flask-WTF tokens enforced on all POST endpoints (`WTF_CSRF_ENABLED=True`).
4. **Secure Image Uploads:** Filenames sanitized via `secure_filename`. Uploads are verified via Pillow `Image.open()`, stripped of metadata, converted to safe RGB JPEG/PNG, and resized to 1200px max bounds.
5. **Anti-Tampering Claims:** Claim limits restrict a user from submitting more than 3 claims on the same found item.

---

## 🧪 Automated Test Suite

A comprehensive `pytest` test suite is provided in the `tests/` directory:

```bash
# Run the entire test suite:
pytest -v
```

### Test Coverage Highlights:
- `tests/test_matching.py`: Verifies TF-IDF and heuristic scores for identical items, mismatched categories, nearby locations, and temporal edge cases.
- `tests/test_workflow.py`: Validates strict state transitions for Lost items, Found items, and Claims lifecycle.
- `tests/test_roles.py`: Asserts that regular users cannot access staff routes (`/kanban`, `/claims/queue`), staff cannot access admin routes (`/admin/settings`), and admins have full access.
- `tests/test_security.py`: Validates NoSQL injection prevention and verifies zero leakage of hidden verification clues to public or regular users.
- `tests/test_duplicates.py`: Tests duplicate warning detection within the time window.
- `tests/test_archive.py`: Validates retention policy evaluation and archive-eligible flagging.

**Result: 17 passed (100% pass rate).**

---

## 🔮 Future Enhancements

1. **Barcode / QR Code Printing:** Generate physical sticker labels for campus custody lockers and item bins.
2. **Optical Character Recognition (OCR):** Auto-extract text from photos of student IDs, driver's licenses, and textbook title pages.
3. **WhatsApp / SMS Gateway Integration:** Dispatch real-time SMS alerts when high-confidence matches (score ≥ 80%) are detected.
4. **Facial Blur on Uploaded Photos:** Automatically detect and blur bystander faces on photos taken in public campus areas.
5. **REST API & Webhooks:** Expose authenticated API endpoints for integration with campus security management systems.
#   F i n d L o o m s  
 