# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from omnexa_accounting.utils.party import get_or_create_web_guest_customer

_WEB_ORDER_POST_SUBMIT_TRANSITIONS = {
	"Invoiced": {"Fulfilled", "Cancelled"},
	"Fulfilled": {"Closed", "Cancelled"},
	"Closed": set(),
	"Cancelled": set(),
}


def _default_income_gl(company: str) -> str | None:
	"""Prefer a leaf **Income** GL for the company; otherwise any non-group GL."""
	acc = frappe.db.get_value(
		"GL Account",
		{"company": company, "is_group": 0, "account_type": "Income"},
		"name",
		order_by="account_number,name",
	)
	if acc:
		return acc
	return frappe.db.get_value(
		"GL Account",
		{"company": company, "is_group": 0},
		"name",
		order_by="account_number,name",
	)


class WebOrder(Document):
	def validate(self):
		self._normalize_legacy_status()
		self._validate_branch_company()
		self._validate_idempotency()
		self._validate_line_companies()
		self._set_line_amounts()
		self._validate_lifecycle_controls()
		self._validate_submitted_status_transition()

	def before_submit(self):
		if self.status not in ("Draft", "Pending Payment"):
			frappe.throw(
				_("Submit only allowed from Draft or Pending Payment (current: {0}).").format(self.status),
				title=_("Order-to-cash"),
			)

	def on_submit(self):
		if self.sales_invoice:
			return
		income_acc = _default_income_gl(self.company)
		if not income_acc:
			frappe.throw(
				_("Configure at least one GL Account for company {0} before checkout.").format(self.company),
				title=_("Accounts"),
			)
		si = frappe.new_doc("Sales Invoice")
		si.company = self.company
		si.currency = frappe.db.get_value("Company", self.company, "default_currency")
		si.customer = get_or_create_web_guest_customer(self.company)
		si.posting_date = frappe.utils.today()
		if self.branch and si.meta.has_field("branch"):
			si.branch = self.branch
		for row in self.lines or []:
			ci_name = row.catalog_item
			slug = frappe.db.get_value("Catalog Item", ci_name, "slug") or ci_name
			si.append(
				"items",
				{
					"item_code": slug,
					"qty": row.qty,
					"rate": row.rate,
					"amount": row.amount,
					"income_account": income_acc,
				},
			)
		si.insert(ignore_permissions=True)
		si.submit()
		self.db_set("sales_invoice", si.name, update_modified=False)
		self.db_set("status", "Invoiced", update_modified=False)

	def _normalize_legacy_status(self):
		if (self.status or "") == "Confirmed":
			self.status = "Invoiced"

	def _validate_branch_company(self):
		if not self.branch:
			return
		bc = frappe.db.get_value("Branch", self.branch, "company")
		if bc and self.company and bc != self.company:
			frappe.throw(_("Branch must belong to the same company."), title=_("Branch"))

	def _validate_submitted_status_transition(self):
		if self.docstatus != 1 or not self.name:
			return
		prev = frappe.db.get_value("Web Order", self.name, "status")
		if not prev or prev == self.status:
			return
		allowed = _WEB_ORDER_POST_SUBMIT_TRANSITIONS.get(prev)
		if allowed is None:
			frappe.throw(
				_("Cannot change status after submit from {0} via this form.").format(prev),
				title=_("Order-to-cash"),
			)
		if self.status not in allowed:
			frappe.throw(
				_("Invalid status transition: {0} → {1}.").format(prev, self.status),
				title=_("Order-to-cash"),
			)

	def _validate_line_companies(self):
		for row in self.lines or []:
			if not row.catalog_item:
				continue
			if frappe.db.get_value("Catalog Item", row.catalog_item, "company") != self.company:
				frappe.throw(
					_("Row {0}: Catalog Item must belong to the same company.").format(row.idx),
					title=_("Company"),
				)

	def _validate_idempotency(self):
		if not self.idempotency_key:
			return
		filters = {"company": self.company, "idempotency_key": self.idempotency_key}
		if self.name:
			filters["name"] = ["!=", self.name]
		if frappe.get_all("Web Order", filters=filters, limit=1):
			frappe.throw(_("Duplicate Idempotency Key for this company."), title=_("Idempotency"))

	def _set_line_amounts(self):
		total = 0
		for row in self.lines or []:
			row.amount = flt(row.qty) * flt(row.rate)
			row.tax_amount = flt(row.tax_amount)
			total += flt(row.amount) + flt(row.tax_amount)
		self.grand_total = total

	def _validate_lifecycle_controls(self):
		if not self.lines:
			frappe.throw(_("At least one order line is required."), title=_("Order"))
		if flt(self.grand_total) <= 0:
			frappe.throw(_("Grand Total must be greater than zero."), title=_("Order"))
		if self.status in {"Pending Payment", "Invoiced", "Fulfilled", "Closed"} and not self.customer_email:
			frappe.throw(_("Customer Email is mandatory once order enters payment/fulfillment lifecycle."), title=_("Customer"))
