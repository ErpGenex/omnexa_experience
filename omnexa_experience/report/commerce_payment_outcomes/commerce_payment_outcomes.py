# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from omnexa_core.omnexa_core.report_print.report_query_filters import (
	get_all_filters,
	policy_version_filters,
	prepare_filters,
	sql_conditions,
)



def execute(filters=None):
	columns = [
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 200},
		{"label": _("Currency (ISO 4217)"), "fieldname": "currency", "fieldtype": "Data", "width": 120},
		{"label": _("Intents"), "fieldname": "intent_count", "fieldtype": "Int", "width": 100},
		{"label": _("Amount total"), "fieldname": "amount_total", "fieldtype": "Currency", "width": 140},
	]
	filters = prepare_filters(filters)
	conditions, params = sql_conditions(filters, "Payment Intent", date_field="creation", company=True, branch=True)
	rows = frappe.db.sql(
		f"""
		SELECT
			pi.status,
			IFNULL(pi.currency, '') AS currency,
			COUNT(*) AS intent_count,
			SUM(IFNULL(pi.amount, 0)) AS amount_total
		FROM `tabPayment Intent`
		WHERE {' AND '.join(conditions)}
		GROUP BY pi.status, IFNULL(pi.currency, '')
		ORDER BY pi.status, currency
		""",
		params,
		as_dict=True,
	)
	return columns, rows
