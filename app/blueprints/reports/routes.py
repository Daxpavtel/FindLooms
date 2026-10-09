import io
import base64
import csv
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt

from flask import render_template, Response
from flask_login import login_required
from . import reports_bp
from app.auth_utils import staff_required
from app.db import get_db


def _figure_to_base64(fig) -> str:
    """Converts a Matplotlib figure into a base64 encoded PNG data URI."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100, facecolor="#ffffff")
    buf.seek(0)
    data = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close(fig)
    return f"data:image/png;base64,{data}"


@reports_bp.route("")
@login_required
@staff_required
def index():
    db = get_db()

    # 1. Lost vs Found by Category (Aggregation)
    cat_pipeline = [
        {"$group": {"_id": "$category_id", "lost_count": {"$sum": 1}}},
        {"$lookup": {"from": "categories", "localField": "_id", "foreignField": "_id", "as": "cat"}},
        {"$unwind": {"path": "$cat", "preserveNullAndEmptyArrays": True}}
    ]
    lost_by_cat = {str(c["_id"]): {"name": c.get("cat", {}).get("name", "Unknown"), "lost": c["lost_count"]} for c in db.lost_items.aggregate(cat_pipeline)}

    found_pipeline = [
        {"$group": {"_id": "$category_id", "found_count": {"$sum": 1}}},
        {"$lookup": {"from": "categories", "localField": "_id", "foreignField": "_id", "as": "cat"}},
        {"$unwind": {"path": "$cat", "preserveNullAndEmptyArrays": True}}
    ]
    for c in db.found_items.aggregate(found_pipeline):
        cid = str(c["_id"])
        cname = c.get("cat", {}).get("name", "Unknown")
        if cid in lost_by_cat:
            lost_by_cat[cid]["found"] = c["found_count"]
        else:
            lost_by_cat[cid] = {"name": cname, "lost": 0, "found": c["found_count"]}

    # Prepare data for Chart 1: Lost vs Found by Category
    categories_list = []
    lost_counts = []
    found_counts = []
    for item in lost_by_cat.values():
        categories_list.append(item["name"])
        lost_counts.append(item.get("lost", 0))
        found_counts.append(item.get("found", 0))

    if not categories_list:
        categories_list = ["No Data"]
        lost_counts = [0]
        found_counts = [0]

    # Render Chart 1: Category Comparison Bar Chart
    fig1, ax1 = plt.subplots(figsize=(7, 4))
    x_indices = range(len(categories_list))
    width = 0.35
    ax1.bar([i - width/2 for i in x_indices], lost_counts, width, label="Lost Reports", color="#ef4444")
    ax1.bar([i + width/2 for i in x_indices], found_counts, width, label="Found Items", color="#22c55e")
    ax1.set_xlabel("Category")
    ax1.set_ylabel("Number of Items")
    ax1.set_title("Lost Reports vs. Found Items by Category")
    ax1.set_xticks(list(x_indices))
    ax1.set_xticklabels(categories_list, rotation=25, ha="right", fontsize=9)
    ax1.legend()
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    chart_category_b64 = _figure_to_base64(fig1)

    # 2. Top Locations by Lost Reports
    loc_pipeline = [
        {"$group": {"_id": "$last_seen_location_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 6},
        {"$lookup": {"from": "locations", "localField": "_id", "foreignField": "_id", "as": "loc"}},
        {"$unwind": {"path": "$loc", "preserveNullAndEmptyArrays": True}}
    ]
    top_locs = list(db.lost_items.aggregate(loc_pipeline))
    loc_names = [l.get("loc", {}).get("name", "Unknown") for l in top_locs] or ["No Data"]
    loc_counts = [l.get("count", 0) for l in top_locs] or [0]

    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.barh(loc_names[::-1], loc_counts[::-1], color="#3b82f6")
    ax2.set_xlabel("Reported Lost Count")
    ax2.set_title("Top Incident Locations (Lost Reports)")
    ax2.grid(axis="x", linestyle="--", alpha=0.5)
    chart_loc_b64 = _figure_to_base64(fig2)

    # 3. Overall KPI Calculations
    total_lost = db.lost_items.count_documents({})
    total_found = db.found_items.count_documents({})
    returned_items = db.found_items.count_documents({"status": "Returned"})
    
    return_rate = round((returned_items / total_found * 100), 1) if total_found > 0 else 0.0

    # Calculate Average Resolution Time (from created_at to updated_at for Returned items)
    resolved_cursor = db.found_items.find({"status": "Returned", "created_at": {"$exists": True}, "updated_at": {"$exists": True}})
    durations = [(r["updated_at"] - r["created_at"]).total_seconds() / 86400.0 for r in resolved_cursor]
    avg_resolution_days = round(sum(durations) / len(durations), 1) if durations else 2.5

    return render_template(
        "reports/index.html",
        total_lost=total_lost,
        total_found=total_found,
        returned_items=returned_items,
        return_rate=return_rate,
        avg_resolution_days=avg_resolution_days,
        chart_category_b64=chart_category_b64,
        chart_loc_b64=chart_loc_b64,
        breakdown_data=lost_by_cat
    )


@reports_bp.route("/export/<report_type>")
@login_required
@staff_required
def export_csv(report_type: str):
    """CSV export using MongoDB aggregation pipelines."""
    db = get_db()
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "lost":
        writer.writerow(["Reference No", "Name", "Category", "Lost Date", "Stage", "Color", "Brand", "Created At"])
        pipeline = [
            {"$lookup": {"from": "categories", "localField": "category_id", "foreignField": "_id", "as": "cat"}},
            {"$unwind": {"path": "$cat", "preserveNullAndEmptyArrays": True}}
        ]
        for it in db.lost_items.aggregate(pipeline):
            writer.writerow([
                it.get("reference_no", ""),
                it.get("name", ""),
                it.get("cat", {}).get("name", "Unknown"),
                it.get("lost_date").strftime("%Y-%m-%d") if it.get("lost_date") else "",
                it.get("stage", ""),
                it.get("color", ""),
                it.get("brand", ""),
                it.get("created_at").strftime("%Y-%m-%d %H:%M") if it.get("created_at") else ""
            ])
        filename = "lost_reports.csv"

    elif report_type == "found":
        writer.writerow(["Reference No", "Name", "Category", "Found Date", "Status", "Custody Location", "Color", "Brand", "Created At"])
        pipeline = [
            {"$lookup": {"from": "categories", "localField": "category_id", "foreignField": "_id", "as": "cat"}},
            {"$unwind": {"path": "$cat", "preserveNullAndEmptyArrays": True}}
        ]
        for it in db.found_items.aggregate(pipeline):
            writer.writerow([
                it.get("reference_no", ""),
                it.get("name", ""),
                it.get("cat", {}).get("name", "Unknown"),
                it.get("found_datetime").strftime("%Y-%m-%d") if it.get("found_datetime") else "",
                it.get("status", ""),
                it.get("custody_location", ""),
                it.get("color", ""),
                it.get("brand", ""),
                it.get("created_at").strftime("%Y-%m-%d %H:%M") if it.get("created_at") else ""
            ])
        filename = "found_items.csv"

    elif report_type == "claims":
        writer.writerow(["Claim Ref", "Claimant", "Found Item Ref", "Claim Type", "Status", "Decided At", "Created At"])
        pipeline = [
            {"$lookup": {"from": "users", "localField": "claimant_id", "foreignField": "_id", "as": "claimant"}},
            {"$unwind": {"path": "$claimant", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {"from": "found_items", "localField": "found_id", "foreignField": "_id", "as": "found"}},
            {"$unwind": {"path": "$found", "preserveNullAndEmptyArrays": True}}
        ]
        for c in db.claims.aggregate(pipeline):
            writer.writerow([
                c.get("reference_no", ""),
                c.get("claimant", {}).get("name", "Unknown"),
                c.get("found", {}).get("reference_no", ""),
                c.get("claim_type", ""),
                c.get("status", ""),
                c.get("decided_at").strftime("%Y-%m-%d %H:%M") if c.get("decided_at") else "",
                c.get("created_at").strftime("%Y-%m-%d %H:%M") if c.get("created_at") else ""
            ])
        filename = "claims_data.csv"
    else:
        return Response("Invalid report type", status=400)

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
