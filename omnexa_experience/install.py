# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe


def _ensure_default_theme():
	if not frappe.db.exists("DocType", "Experience Tenant Theme"):
		return
	company = frappe.db.get_value("Company", {}, "name")
	if not company:
		return
	row = frappe.db.get_value(
		"Experience Tenant Theme",
		{"company": company, "theme_preset": "erpgenex_theme_0426"},
		"name",
	)
	if row:
		return
	doc = frappe.new_doc("Experience Tenant Theme")
	doc.company = company
	doc.theme_preset = "erpgenex_theme_0426"
	doc.apply_to_desk = 0 if frappe.db.exists("Experience Tenant Theme", {"company": company, "apply_to_desk": 1}) else 1
	doc.apply_to_public_site = 0 if frappe.db.exists("Experience Tenant Theme", {"apply_to_public_site": 1}) else 1
	doc.insert(ignore_permissions=True)


def after_install():
	_ensure_default_theme()


def after_migrate():
	_ensure_default_theme()
