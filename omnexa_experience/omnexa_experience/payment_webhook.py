# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from omnexa_core.omnexa_core.webhook import WebhookRejectedError, process_webhook_event

ALLOWED_PAYMENT_INTENT_STATUS = {
	"requires_payment_method",
	"processing",
	"succeeded",
	"failed",
}


def process_payment_intent_webhook(
	event_id: str,
	payload: dict,
	received_signature: str = "",
	secret: str = "",
):
	if not secret:
		secret = frappe.conf.get("omnexa_payment_webhook_secret", "")

	def processor(data: dict):
		intent_name = (data or {}).get("payment_intent")
		if not intent_name:
			raise WebhookRejectedError(_("payment_intent is required."))
		status = (data.get("status") or "").strip()
		if status not in ALLOWED_PAYMENT_INTENT_STATUS:
			raise WebhookRejectedError(_("Invalid payment status received from webhook."))
		doc = frappe.get_doc("Payment Intent", intent_name)
		ref = (data.get("provider_reference") or "").strip()
		if ref:
			doc.client_secret_ref = ref
			if status in {"processing", "succeeded", "refunded"} and not doc.payment_reference:
				doc.payment_reference = ref
		if status == "succeeded" and doc.status in {"requires_payment_method", "requires_confirmation"}:
			doc.status = "processing"
			doc.save(ignore_permissions=True)
			doc.reload()
		doc.status = status
		doc.save(ignore_permissions=True)

	return process_webhook_event(
		provider="psp_dummy",
		event_id=event_id,
		payload=payload,
		processor=processor,
		received_signature=received_signature,
		secret=secret,
	)
