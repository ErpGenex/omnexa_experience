# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe


def get_context(context):
	path = (frappe.local.request.path if frappe.local.request else "") or ""
	parts = [p for p in path.split("/") if p]
	context.vertical = parts[-1] if parts and parts[-1] != "vertical" else frappe.form_dict.get("vertical") or ""
