import calendar
from datetime import datetime, date
from flask import render_template, request, abort
from flask_login import current_user

from . import views_bp
from app.db import get_db
from app.repositories.items import get_lost_items, get_found_items


# ==========================================
# CALENDAR VIEWS (SERVER-RENDERED)
# ==========================================

@views_bp.route("/calendar")
def calendar_view():
    """Server-rendered month calendar grid built with Python calendar module."""
    db = get_db()
    today = date.today()
    
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))

    # Calculate prev and next month
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    month_name = calendar.month_name[month]
    month_days = calendar.Calendar(firstweekday=0).monthdays2calendar(year, month)

    start_dt = datetime(year, month, 1)
    end_dt = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)

    # Fetch items for this month
    lost_cur = db.lost_items.find({"lost_date": {"$gte": start_dt, "$lte": end_dt}})
    found_cur = db.found_items.find({"found_datetime": {"$gte": start_dt, "$lte": end_dt}})
    handover_cur = db.handovers.find({"scheduled_datetime": {"$gte": start_dt, "$lte": end_dt}})

    # Aggregate counts by day
    events_by_day = {}
    for it in lost_cur:
        d = it["lost_date"].day
        events_by_day.setdefault(d, {"lost": 0, "found": 0, "handovers": 0})
        events_by_day[d]["lost"] += 1

    for it in found_cur:
        d = it["found_datetime"].day
        events_by_day.setdefault(d, {"lost": 0, "found": 0, "handovers": 0})
        events_by_day[d]["found"] += 1

    for h in handover_cur:
        if h.get("scheduled_datetime"):
            d = h["scheduled_datetime"].day
            events_by_day.setdefault(d, {"lost": 0, "found": 0, "handovers": 0})
            events_by_day[d]["handovers"] += 1

    return render_template(
        "views/calendar.html",
        year=year,
        month=month,
        month_name=month_name,
        month_days=month_days,
        events_by_day=events_by_day,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        today=today
    )


@views_bp.route("/calendar/day/<date_str>")
def day_view(date_str: str):
    """Detailed view for a specific day showing lost items, found items, and scheduled returns."""
    db = get_db()
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        abort(400)

    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())

    is_staff = current_user.is_authenticated and current_user.is_staff

    lost_items, _ = get_lost_items(
        filter_query={"lost_date": {"$gte": start_dt, "$lte": end_dt}},
        limit=50,
        is_staff=is_staff
    )
    found_items, _ = get_found_items(
        filter_query={"found_datetime": {"$gte": start_dt, "$lte": end_dt}},
        limit=50,
        is_staff=is_staff
    )
    
    handovers = list(db.handovers.find({"scheduled_datetime": {"$gte": start_dt, "$lte": end_dt}}))
    for h in handovers:
        h["claim"] = db.claims.find_one({"_id": h["claim_id"]})

    return render_template(
        "views/day.html",
        target_date=target_date,
        date_str=date_str,
        lost_items=lost_items,
        found_items=found_items,
        handovers=handovers,
        is_staff=is_staff
    )
