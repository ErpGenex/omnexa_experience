# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document

_PAYMENT_INTENT_TRANSITIONS = {
	"requires_payment_method": {"requires_confirmation", "processing", "canceled", "failed"},
	"requires_confirmation": {"processing", "canceled", "failed"},
	"processing": {"succeeded", "failed", "canceled"},
	"succeeded": {"refunded"},
	"failed": set(),
	"canceled": set(),
	"refunded": set(),
}


class PaymentIntent(Document):
	def validate(self):
		if self.web_order and frappe.db.get_value("Web Order", self.web_order, "company") != self.company:
			frappe.throw(_("Web Order must belong to the same company."), title=_("Validation"))
		self._validate_status_transition()

	def _validate_status_transition(self):
		if not self.name:
			return
		prev = frappe.db.get_value("Payment Intent", self.name, "status")
		if not prev or prev == self.status:
			return
		allowed = _PAYMENT_INTENT_TRANSITIONS.get(prev)
		if allowed is None:
			return
		if self.status not in allowed:
			frappe.throw(
				_("Invalid payment intent status transition: {0} → {1}.").format(prev, self.status),
				title=_("Payment"),
			)
