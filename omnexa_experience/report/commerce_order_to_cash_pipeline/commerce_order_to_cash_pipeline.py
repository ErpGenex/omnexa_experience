# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Order-to-cash funnel by Web Order status (IFRS 15 / ASC 606 friendly segmentation)."""

import frappe
from frappe import _
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
		"wo.company = %(company)s",
		"DATE(wo.modified) BETWEEN %(from_date)s AND %(to_date)s",
	]
	allowed = get_allowed_branches(company=filters.company)
	if allowed is not None:
		if not allowed:
			return _columns(), []
		params["allowed_branches"] = tuple(allowed)
		conditions.append("(IFNULL(wo.branch, '') = '' OR wo.branch IN %(allowed_branches)s)")
	if filters.get("branch"):
		conditions.append("wo.branch = %(branch)s")
		params["branch"] = filters.branch

	rows = frappe.db.sql(
		f"""
		SELECT
			IFNULL(wo.commerce_segment, '') AS commerce_segment,
			IFNULL(wo.branch, '') AS branch,
			wo.status,
			COUNT(*) AS order_count,
			SUM(IFNULL(wo.grand_total, 0)) AS grand_total,
			SUM(IF(wo.sales_invoice IS NOT NULL AND wo.sales_invoice != '', 1, 0)) AS invoiced_count
		FROM `tabWeb Order` wo
		WHERE {' AND '.join(conditions)}
		GROUP BY IFNULL(wo.commerce_segment, ''), IFNULL(wo.branch, ''), wo.status
		ORDER BY commerce_segment, branch, wo.status
		""",
		params,
		as_dict=True,
	)
	for r in rows:
		r["grand_total"] = flt(r.get("grand_total"), 2)
		r["order_count"] = int(r.get("order_count") or 0)
		r["invoiced_count"] = int(r.get("invoiced_count") or 0)
	return _columns(), rows


def _columns():
	return [
		{"label": _("Commerce segment"), "fieldname": "commerce_segment", "fieldtype": "Data", "width": 160},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Data", "width": 140},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 140},
		{"label": _("Orders"), "fieldname": "order_count", "fieldtype": "Int", "width": 90},
		{"label": _("Invoiced lines"), "fieldname": "invoiced_count", "fieldtype": "Int", "width": 110},
		{"label": _("Grand total"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 130},
	]
