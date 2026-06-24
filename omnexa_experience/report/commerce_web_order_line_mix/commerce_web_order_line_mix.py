# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Catalog / performance-obligation line mix from submitted Web Orders (IFRS 15 distinct goods or services at line level)."""

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
		SELECT
			IFNULL(wo.commerce_segment, '') AS commerce_segment,
			IFNULL(wo.order_channel, '') AS order_channel,
			IFNULL(wol.catalog_item, '') AS catalog_item,
			SUM(IFNULL(wol.qty, 0)) AS qty_sold,
			SUM(IFNULL(wol.amount, 0)) AS amount_net,
			SUM(IFNULL(wol.tax_amount, 0)) AS tax_amount,
			COUNT(DISTINCT wo.name) AS order_count
		FROM `tabWeb Order` wo
		INNER JOIN `tabWeb Order Line` wol ON wol.parent = wo.name AND wol.parenttype = 'Web Order'
		WHERE {' AND '.join(conditions)}
		GROUP BY IFNULL(wo.commerce_segment, ''), IFNULL(wo.order_channel, ''), IFNULL(wol.catalog_item, '')
		ORDER BY commerce_segment, order_channel, amount_net DESC
		""",
		params,
		as_dict=True,
	)
	for r in rows:
		r["qty_sold"] = flt(r.get("qty_sold"), 3)
		r["amount_net"] = flt(r.get("amount_net"), 2)
		r["tax_amount"] = flt(r.get("tax_amount"), 2)
		r["order_count"] = int(r.get("order_count") or 0)
	columns = _columns()
	chart = auto_chart_for_columns(rows, columns)
	return columns, rows, None, chart


def _columns():
	return [
		{"label": _("Commerce segment"), "fieldname": "commerce_segment", "fieldtype": "Data", "width": 160},
		{"label": _("Order channel"), "fieldname": "order_channel", "fieldtype": "Data", "width": 120},
		{"label": _("Catalog item"), "fieldname": "catalog_item", "fieldtype": "Data", "width": 200},
		{"label": _("Qty sold"), "fieldname": "qty_sold", "fieldtype": "Float", "width": 100},
		{"label": _("Amount (net)"), "fieldname": "amount_net", "fieldtype": "Currency", "width": 130},
		{"label": _("Tax"), "fieldname": "tax_amount", "fieldtype": "Currency", "width": 110},
		{"label": _("Orders"), "fieldname": "order_count", "fieldtype": "Int", "width": 90},
	]
