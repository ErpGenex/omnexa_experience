# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Order-to-cash cycle time KPIs (submitted Web Orders): proxy days from document creation to last modification by status — ISO 9001 / lean O2C monitoring."""

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
		"wo.docstatus = 1",
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
			IFNULL(wo.order_channel, '') AS order_channel,
			IFNULL(wo.branch, '') AS branch,
			wo.status,
			COUNT(*) AS order_count,
			AVG(
				CASE
					WHEN wo.status IN ('Invoiced', 'Fulfilled', 'Closed')
						AND wo.sales_invoice IS NOT NULL AND wo.sales_invoice != ''
					THEN DATEDIFF(DATE(wo.modified), DATE(wo.creation))
					ELSE NULL
				END
			) AS avg_days_to_invoice_proxy,
			AVG(
				CASE
					WHEN wo.status IN ('Fulfilled', 'Closed')
					THEN DATEDIFF(DATE(wo.modified), DATE(wo.creation))
					ELSE NULL
				END
			) AS avg_days_to_fulfillment_proxy
		FROM `tabWeb Order` wo
		WHERE {' AND '.join(conditions)}
		GROUP BY IFNULL(wo.commerce_segment, ''), IFNULL(wo.order_channel, ''), IFNULL(wo.branch, ''), wo.status
		ORDER BY commerce_segment, order_channel, branch, wo.status
		""",
		params,
		as_dict=True,
	)
	for r in rows:
		r["order_count"] = int(r.get("order_count") or 0)
		r["avg_days_to_invoice_proxy"] = flt(r.get("avg_days_to_invoice_proxy"), 2)
		r["avg_days_to_fulfillment_proxy"] = flt(r.get("avg_days_to_fulfillment_proxy"), 2)
	return _columns(), rows


def _columns():
	return [
		{"label": _("Commerce segment"), "fieldname": "commerce_segment", "fieldtype": "Data", "width": 160},
		{"label": _("Order channel"), "fieldname": "order_channel", "fieldtype": "Data", "width": 120},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Data", "width": 140},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Orders"), "fieldname": "order_count", "fieldtype": "Int", "width": 90},
		{
			"label": _("Avg days to invoice (proxy)"),
			"fieldname": "avg_days_to_invoice_proxy",
			"fieldtype": "Float",
			"width": 170,
		},
		{
			"label": _("Avg days to fulfillment (proxy)"),
			"fieldname": "avg_days_to_fulfillment_proxy",
			"fieldtype": "Float",
			"width": 190,
		},
	]
