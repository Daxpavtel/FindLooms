# LostFound: Comprehensive Demo Script & Presentation Guide

This document provides a complete, click-by-click demonstration script for showcasing all 6 user journeys and core features of the **LostFound** system.

---

## 🏁 Preparation & Setup

1. **Start the local server:**
   ```bash
   python run.py
   ```
2. **Open browser:** Navigate to `http://127.0.0.1:5000`
3. **Keep demo credentials handy:**
   - **Admin:** `admin@campus.edu` / `AdminPass123!`
   - **Staff:** `priya.sharma@campus.edu` / `StaffPass123!`
   - **User 1:** `aarav.patel@campus.edu` / `UserPass123!`
   - **User 2:** `rohan.verma@campus.edu` / `UserPass123!`

---

## 🎯 Journey 1: Public Discovery & Reporting a Lost Item (Student Persona)

**Goal:** Demonstrate user authentication, responsive zero-JS reporting, and secret verification protection.

1. **Public Landing Page (`/`):**
   - Point out key KPI counters at the top: *Total Lost, Total Found, Reunited, Active Claims*.
   - Point out the **Zero-JS architecture** (no scripts loaded in network tab).
   - Click **"Browse Found Items"** or click **"Found Items"** in navbar.
   - Click any item card (e.g. *MacBook Pro 14 Laptop*).
   - **Showcase Privacy:** Highlight that only public descriptions and general custody locations are visible. The *Secret Verification Clue* is completely absent from the page.

2. **Sign In (`/auth/login`):**
   - Click **"Sign In"** in top navbar.
   - Enter Email: `aarav.patel@campus.edu`
   - Enter Password: `UserPass123!`
   - Click **"Sign In"**.
   - Notice the personalized **Dashboard (`/auth/dashboard`)** with Aarav's active reports and quick actions.

3. **Report a Lost Item (`/lost/new`):**
   - Click **"Report Lost Item"** button.
   - Fill out the form:
     - **Title:** `Midnight Blue Sony WH-1000XM5 Headphones`
     - **Category:** Select `Electronics`
     - **Primary Color:** `Midnight Blue`
     - **Brand:** `Sony`
     - **Date Lost:** Today's date
     - **Approximate Time:** `Around 3:15 PM`
     - **Last Seen Location:** Select `Central Library Custody Desk` or `Main Library Reading Room`
     - **Public Description:** `Sony wireless noise-canceling over-ear headphones in grey zippered case.`
     - **Secret Verification Clue (Hidden):** `Inside zipper mesh pocket has a USB-C charging cable with orange tape around the plug.`
   - Click **"Submit Lost Report"**.
   - **Outcome:** System assigns a reference number (`LST-2026-0002`). The user is redirected to the item detail page showing status `Reported`.

---

## 🎯 Journey 2: Staff Intake & Duplicate Warning (Staff Persona)

**Goal:** Demonstrate staff authentication, found item intake, and duplicate detection.

1. **Switch to Staff Account:**
   - Click **"Sign Out"** in user dropdown.
   - Click **"Sign In"** and enter:
     - Email: `priya.sharma@campus.edu`
     - Password: `StaffPass123!`
   - Notice that staff view unlocks new navigation items: **Kanban**, **Claims**, **Map**, **Calendar**, **Reports**.

2. **Register a Discovered Item (`/found/new`):**
   - Click **"Register Found"** in the top navigation.
   - Fill in:
     - **Title:** `Sony WH-1000XM5 Over-Ear Headphones`
     - **Category:** `Electronics`
     - **Found Date/Time:** Today's date
     - **Found Location:** `Main Library Reading Room`
     - **Color:** `Blue`
     - **Brand:** `Sony`
     - **Public Description:** `Found blue Sony wireless headphones in black carry case on second floor desk.`
     - **Confidential Inspection Clue:** `Orange tape on black USB charging cable inside mesh pouch.`
     - **Custody Location:** `Library Security Safe Bin 3`
   - Click **"Register Found Item"**.
   - **Outcome:** Item registered with sequential reference (`FND-2026-0002`).

---

## 🎯 Journey 3: Intelligent Matching & Candidate Breakdown

**Goal:** Demonstrate Scikit-Learn TF-IDF similarity and multi-factor mathematical scoring.

1. **Review Item Matches:**
   - On the newly created Found Item detail page, look at the **"Possible Matches"** section.
   - Notice the candidate match linking `Sony WH-1000XM5 Over-Ear Headphones` to Aarav's lost headphones!
   - Highlight the **Match Score Badge** (Score: ~**92%**).
   - Click **"Score Breakdown"**:
     - *Category Match: 30 / 30 pts*
     - *TF-IDF Text Similarity: 22.5 / 25 pts*
     - *Location Proximity: 20 / 20 pts*
     - *Color Match: 10 / 10 pts*
     - *Brand Match: 10 / 10 pts*
   - Note that both items have automatically transitioned from `Reported`/`Unmatched` to `Possible Match`.

---

## 🎯 Journey 4: Claim Filing & Side-by-Side Staff Verification

**Goal:** Demonstrate claimant proof submission and dual-column fraud prevention view.

1. **Student Files Ownership Claim:**
   - Sign out of Priya's account and log back in as `aarav.patel@campus.edu` (`UserPass123!`).
   - On Found Item `FND-2026-0002` detail page, click **"File Ownership Claim"**.
   - Enter Proof Answer:
     - *"The headphones are in a zippered travel case. Inside the mesh pocket, there is a short charging cord with bright orange tape on one end."*
   - Click **"Submit Claim"**.
   - Notice claim reference (`CLM-2026-0001`) created in `New` status.

2. **Staff Reviews Claim:**
   - Sign out and log back in as `priya.sharma@campus.edu` (`StaffPass123!`).
   - Navigate to **"Claims"** (`/claims`).
   - Filter by **"New"** tab.
   - Click **"Review Claim"** on Aarav's claim.

3. **Dual-Pane Side-by-Side Screen (`/claims/<id>/review`):**
   - **Left Pane (Claimant's Submission):** Displays Aarav's proof description and timestamp.
   - **Right Pane (Confidential Custody Record):** Displays the finder's hidden custody note: *"Orange tape on black USB charging cable"*.
   - Staff compares the two clues side-by-side.
   - Staff selects **"Approve Claim"** radio button and enters notes: *"Proof verified against custody cable marking."*
   - Click **"Submit Decision"**.
   - **Outcome:** Claim is marked `Approved`, Found Item status updates to `Claimed`.

---

## 🎯 Journey 5: Physical Custody Handover & Resolution

**Goal:** Demonstrate custody chain-of-custody transfer and resolution.

1. **Execute Handover (`/claims/<id>/handover`):**
   - From the approved claim detail page, click **"Schedule / Complete Handover"**.
   - Enter Receiver Name: `Aarav Patel`
   - Enter Date: Today's date
   - Enter Acknowledgement Note: `Student verified with University ID #90422. Item handed over in good condition.`
   - Click **"Record Physical Handover"**.
   - **Outcome:**
     - Claim status updates to `Returned`.
     - Found item status updates to `Returned`.
     - Lost item stage updates to `Closed`.
     - Permanent handover record stored with custodian stamp.

---

## 🎯 Journey 6: Visual Kanban, Map, Calendar, and Analytics

**Goal:** Demonstrate zero-JS visual views and reporting pipelines.

1. **CSS Kanban Board (`/kanban`):**
   - Navigate to **"Kanban"** in the top navigation.
   - Observe 5 swimlanes: *Unmatched, Possible Match, Under Review, Handed Over, Closed*.
   - Point out items in each lane with status badges.
   - Click the **"Move Stage"** button to demonstrate server-rendered stage progression without any client-side JavaScript.

2. **Server-Rendered Campus Map (`/views/map`):**
   - Navigate to **"Map"** in navigation.
   - Observe the Folium campus map rendered within an embedded iframe.
   - Filter by Zone (e.g. *Academic Core*, *Residential*) and Building (*Main Library*).
   - Click markers to view item count popups for each location.

3. **Month Calendar Grid (`/views/calendar`):**
   - Navigate to **"Calendar"** in navigation.
   - Observe current month grid with color-coded badges indicating items lost (orange) and found (green) on specific days.
   - Click on any day number to view the **Day Schedule Detail View** showing item timelines.

4. **Analytics & Reports (`/reports`):**
   - Navigate to **"Reports"**.
   - View KPI summary: Total Volume, Resolution Rate %, Average Days to Claim.
   - Inspect headless Matplotlib charts:
     - Monthly Volume Bar Chart
     - Category Distribution Chart
   - Click **"Export CSV"** to download raw reporting data.

5. **Admin Settings & Audit Log (`/admin/settings`, `/admin/audit`):**
   - Sign in as `admin@campus.edu` (`AdminPass123!`).
   - Navigate to **"Admin Settings"** to show retention threshold configuration (default 30 days) and match threshold (60 pts).
   - Navigate to **"Audit Log"** to show the immutable log tracking every registration, review, decision, and handover event.

---

## 🏁 Summary of Acceptance Criteria Met

- [x] Full-stack Flask + MongoDB (PyMongo) web application.
- [x] STRICT Zero-JavaScript architecture (0 script tags, 0 .js files).
- [x] Multi-factor explainable matching engine (0–100 score).
- [x] Hidden verification detail with zero data leakage.
- [x] Side-by-side claim verification screen.
- [x] Handover logging and chain of custody.
- [x] CSS Kanban board, server-rendered Map, and Calendar grid.
- [x] APScheduler daily retention auto-archive.
- [x] 17/17 automated pytest tests passing.
- [x] 13/13 live server verification steps verified.
