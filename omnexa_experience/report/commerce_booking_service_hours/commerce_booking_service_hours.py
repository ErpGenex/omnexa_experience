# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Delivered service duration by resource (completed bookings) — ISO capacity / service delivery view."""

import frappe
from frappe import _

from omnexa_core.omnexa_core.utils.report_charts import auto_chart_for_columns
from frappe.utils import flt

from omnexa_core.omnexa_core.branch_access import get_allowed_branches


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required."), title=_("Filters"))

	params = {"company": filters.company, "from_date": filters.from_date, "to_date": filters.to_date}
	conditions = [
		"b.company = %(company)s",
		"b.status = 'Completed'",
		"DATE(b.modified) BETWEEN %(from_date)s AND %(to_date)s",
	]
	allowed = get_allowed_branches(company=filters.company)
	if allowed is not None:
		if not allowed:
			return _columns(), []
		params["allowed_branches"] = tuple(allowed)
		conditions.append("(IFNULL(b.branch, '') = '' OR b.branch IN %(allowed_branches)s)")
	if filters.get("branch"):
		conditions.append("b.branch = %(branch)s")
		params["branch"] = filters.branch

	rows = frappe.db.sql(
		f"""
		SELECT
			IFNULL(b.commerce_segment, '') AS commerce_segment,
			IFNULL(b.branch, '') AS branch,
			b.bookable_resource,
			COUNT(*) AS completed_bookings,
			SUM(TIMESTAMPDIFF(MINUTE, b.start_datetime, b.end_datetime)) AS service_minutes_total,
			AVG(TIMESTAMPDIFF(MINUTE, b.start_datetime, b.end_datetime)) AS service_minutes_avg
		FROM `tabBooking` b
		WHERE {' AND '.join(conditions)}
		  AND b.start_datetime IS NOT NULL AND b.end_datetime IS NOT NULL
		  AND b.end_datetime > b.start_datetime
		GROUP BY IFNULL(b.commerce_segment, ''), IFNULL(b.branch, ''), b.bookable_resource
		ORDER BY commerce_segment, branch, bookable_resource
		""",
		params,
		as_dict=True,
	)
	for r in rows:
		r["completed_bookings"] = int(r.get("completed_bookings") or 0)
		r["service_minutes_total"] = flt(r.get("service_minutes_total"), 2)
		r["service_minutes_avg"] = flt(r.get("service_minutes_avg"), 2)
		r["service_hours_total"] = flt((r.get("service_minutes_total") or 0) / 60.0, 2)
	columns = _columns()
	chart = auto_chart_for_columns(rows, columns)
	return columns, rows, None, chart


def _columns():
	return [
		{"label": _("Commerce segment"), "fieldname": "commerce_segment", "fieldtype": "Data", "width": 160},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Data", "width": 140},
		{"label": _("Bookable resource"), "fieldname": "bookable_resource", "fieldtype": "Data", "width": 180},
		{"label": _("Completed bookings"), "fieldname": "completed_bookings", "fieldtype": "Int", "width": 140},
		{"label": _("Service minutes (total)"), "fieldname": "service_minutes_total", "fieldtype": "Float", "width": 160},
		{"label": _("Service minutes (avg)"), "fieldname": "service_minutes_avg", "fieldtype": "Float", "width": 160},
		{"label": _("Service hours (total)"), "fieldname": "service_hours_total", "fieldtype": "Float", "width": 150},
	]
