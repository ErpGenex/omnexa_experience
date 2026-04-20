# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Payment intent outcomes (PSD2 / card-scheme style status taxonomy at summary level)."""

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required."), title=_("Filters"))

	params = {"company": filters.company, "from_date": filters.from_date, "to_date": filters.to_date}
	rows = frappe.db.sql(
		"""
		SELECT
			pi.status,
			IFNULL(pi.currency, '') AS currency,
			COUNT(*) AS intent_count,
			SUM(IFNULL(pi.amount, 0)) AS amount_total
		FROM `tabPayment Intent` pi
		WHERE pi.company = %(company)s
		  AND DATE(pi.modified) BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY pi.status, IFNULL(pi.currency, '')
		ORDER BY pi.status, currency
		""",
		params,
		as_dict=True,
	)
	for r in rows:
		r["intent_count"] = int(r.get("intent_count") or 0)
		r["amount_total"] = flt(r.get("amount_total"), 2)
	return _columns(), rows


def _columns():
	return [
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 200},
		{"label": _("Currency (ISO 4217)"), "fieldname": "currency", "fieldtype": "Data", "width": 120},
		{"label": _("Intents"), "fieldname": "intent_count", "fieldtype": "Int", "width": 100},
		{"label": _("Amount total"), "fieldname": "amount_total", "fieldtype": "Currency", "width": 140},
	]
