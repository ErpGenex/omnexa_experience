# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Booking lifecycle by status and resource (operations / SLA view)."""

import frappe
from frappe import _

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
			b.status,
			COUNT(*) AS booking_count
		FROM `tabBooking` b
		WHERE {' AND '.join(conditions)}
		GROUP BY IFNULL(b.commerce_segment, ''), IFNULL(b.branch, ''), b.bookable_resource, b.status
		ORDER BY commerce_segment, branch, bookable_resource, b.status
		""",
		params,
		as_dict=True,
	)
	for r in rows:
		r["booking_count"] = int(r.get("booking_count") or 0)
	return _columns(), rows


def _columns():
	return [
		{"label": _("Commerce segment"), "fieldname": "commerce_segment", "fieldtype": "Data", "width": 160},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Data", "width": 140},
		{"label": _("Bookable resource"), "fieldname": "bookable_resource", "fieldtype": "Data", "width": 180},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Bookings"), "fieldname": "booking_count", "fieldtype": "Int", "width": 100},
	]
