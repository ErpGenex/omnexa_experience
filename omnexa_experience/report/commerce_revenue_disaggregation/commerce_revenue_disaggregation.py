# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Revenue and line-level disaggregation by segment, channel, and branch (IFRS 8 operating segments + IFRS 15 disaggregation of revenue)."""

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
		WITH wo_base AS (
			SELECT name, commerce_segment, order_channel, branch, status, grand_total
			FROM `tabWeb Order` wo
			WHERE {' AND '.join(conditions)}
		),
		line_agg AS (
			SELECT wol.parent AS web_order,
				SUM(IFNULL(wol.amount, 0)) AS line_net,
				SUM(IFNULL(wol.tax_amount, 0)) AS line_tax
			FROM `tabWeb Order Line` wol
			INNER JOIN wo_base b ON b.name = wol.parent AND wol.parenttype = 'Web Order'
			GROUP BY wol.parent
		)
		SELECT
			IFNULL(b.commerce_segment, '') AS commerce_segment,
			IFNULL(b.order_channel, '') AS order_channel,
			IFNULL(b.branch, '') AS branch,
			b.status,
			COUNT(DISTINCT b.name) AS order_count,
			SUM(IFNULL(b.grand_total, 0)) AS grand_total,
			SUM(IFNULL(l.line_net, 0)) AS line_net,
			SUM(IFNULL(l.line_tax, 0)) AS line_tax
		FROM wo_base b
		LEFT JOIN line_agg l ON l.web_order = b.name
		GROUP BY IFNULL(b.commerce_segment, ''), IFNULL(b.order_channel, ''), IFNULL(b.branch, ''), b.status
		ORDER BY commerce_segment, order_channel, branch, b.status
		""",
		params,
		as_dict=True,
	)
	for r in rows:
		r["order_count"] = int(r.get("order_count") or 0)
		r["grand_total"] = flt(r.get("grand_total"), 2)
		r["line_net"] = flt(r.get("line_net"), 2)
		r["line_tax"] = flt(r.get("line_tax"), 2)
		r["line_gross"] = flt((r.get("line_net") or 0) + (r.get("line_tax") or 0), 2)
	columns = _columns()
	chart = auto_chart_for_columns(rows, columns)
	return columns, rows, None, chart


def _columns():
	return [
		{"label": _("Commerce segment"), "fieldname": "commerce_segment", "fieldtype": "Data", "width": 160},
		{"label": _("Order channel"), "fieldname": "order_channel", "fieldtype": "Data", "width": 120},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Data", "width": 140},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Orders"), "fieldname": "order_count", "fieldtype": "Int", "width": 90},
		{"label": _("Grand total (header)"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 150},
		{"label": _("Line net"), "fieldname": "line_net", "fieldtype": "Currency", "width": 120},
		{"label": _("Line tax"), "fieldname": "line_tax", "fieldtype": "Currency", "width": 110},
		{"label": _("Line net + tax"), "fieldname": "line_gross", "fieldtype": "Currency", "width": 130},
	]
