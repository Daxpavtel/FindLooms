import calendar
from datetime import datetime, date
from flask import render_template, request, abort, url_for, Response
from flask_login import current_user
import folium

from . import views_bp
from app.db import get_db
from app.repositories.locations import get_location_by_id, get_zones, get_buildings
from app.repositories.items import get_lost_items, get_found_items, _populate_item_relations


# ==========================================
# MAP VIEWS (FOLIUM)
# ==========================================

@views_bp.route("/map")
def map_view():
    """Renders the map view page with GET filter form and embedded Folium iframe."""
    zones = get_zones()
    buildings = get_buildings()

    zone_filter = request.args.get("zone", "")
    building_filter = request.args.get("building", "")

    return render_template(
        "views/map.html",
        zones=zones,
        buildings=buildings,
        current_zone=zone_filter,
        current_building=building_filter
    )


@views_bp.route("/map/embed")
def map_embed():
    """Generates the Folium map HTML for the iframe."""
    db = get_db()
    zone_filter = request.args.get("zone", "").strip()
    building_filter = request.args.get("building", "").strip()

    query = {"is_active": True}
    if zone_filter:
        query["zone"] = zone_filter
    if building_filter:
        query["building"] = building_filter

    locations = list(db.locations.find(query))

    # Determine map center (Default: Indus University, Rancharda, Via Shilaj, Gujarat 382115)
    INDUS_LAT, INDUS_LNG = 23.0850, 72.4550

    valid_coords = [(loc["latitude"], loc["longitude"]) for loc in locations if loc.get("latitude") and loc.get("longitude")]
    if valid_coords:
        avg_lat = sum(c[0] for c in valid_coords) / len(valid_coords)
        avg_lng = sum(c[1] for c in valid_coords) / len(valid_coords)
    else:
        avg_lat, avg_lng = INDUS_LAT, INDUS_LNG

    m = folium.Map(location=[avg_lat, avg_lng], zoom_start=16, tiles="OpenStreetMap")

    for loc in locations:
        lat = loc.get("latitude")
        lng = loc.get("longitude")
        if not lat or not lng:
            continue

        loc_id = loc["_id"]
        # Count active items
        lost_count = db.lost_items.count_documents({
            "last_seen_location_id": loc_id,
            "stage": {"$nin": ["Returned", "Archived"]}
        })
        found_count = db.found_items.count_documents({
            "found_location_id": loc_id,
            "status": {"$nin": ["Returned", "Archived"]}
        })

        color = "red" if lost_count > 0 and found_count == 0 else ("green" if found_count > 0 and lost_count == 0 else "blue")
        
        detail_url = url_for("views.location_detail", loc_id=str(loc_id))
        
        popup_html = f"""
        <div style="font-family: sans-serif; min-width: 180px;">
            <h6 style="margin: 0 0 4px 0; font-weight: bold;">{loc['name']}</h6>
            <div style="font-size: 12px; color: #666; margin-bottom: 8px;">{loc.get('building')} • {loc.get('zone')}</div>
            <div style="margin-bottom: 8px;">
                <span style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-size: 11px;">Lost: <b>{lost_count}</b></span>
                <span style="background: #dcfce7; color: #166534; padding: 2px 6px; border-radius: 4px; font-size: 11px;">Found: <b>{found_count}</b></span>
            </div>
            <a href="{detail_url}" target="_top" style="display: inline-block; background: #2563eb; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 11px; text-decoration: none;">View Active Reports</a>
        </div>
        """
        
        folium.Marker(
            location=[lat, lng],
            tooltip=f"{loc['name']} (Lost: {lost_count}, Found: {found_count})",
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    return Response(m.get_root().render(), mimetype="text/html")


@views_bp.route("/location/<loc_id>")
def location_detail(loc_id: str):
    """Shows all active lost and found items associated with a given location."""
    loc = get_location_by_id(loc_id)
    if not loc:
        abort(404)

    is_staff = current_user.is_authenticated and current_user.is_staff
    lost_items, _ = get_lost_items(
        filter_query={"last_seen_location_id": loc["_id"], "stage": {"$nin": ["Returned", "Archived"]}},
        limit=50,
        is_staff=is_staff
    )
    found_items, _ = get_found_items(
        filter_query={"found_location_id": loc["_id"], "status": {"$nin": ["Returned", "Archived"]}},
        limit=50,
        is_staff=is_staff
    )

    return render_template(
        "views/location_detail.html",
        location=loc,
        lost_items=lost_items,
        found_items=found_items
    )


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
