# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_experience.omnexa_experience.activity_website_registry import resolve_legacy_redirect


def get_context(context):
	target = resolve_legacy_redirect(frappe.request.path if frappe.request else "/campus/programs") or "/education/programs"
	qs = frappe.request.query_string if frappe.request else b""
	if qs:
		if isinstance(qs, bytes):
			qs = qs.decode()
		target = f"{target}?{qs}"
	frappe.local.flags.redirect_location = target
