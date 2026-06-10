# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe

SUPPORTED_FRAPPE_MAJOR = 15


def enforce_supported_frappe_version():
	"""Fail fast when running on unsupported Frappe major versions."""
	version_text = (getattr(frappe, "__version__", "") or "").strip()
	if not version_text:
		return

	major_token = version_text.split(".", 1)[0]
	try:
		major = int(major_token)
	except ValueError:
		return

	if major != SUPPORTED_FRAPPE_MAJOR:
		frappe.throw(
			f"Unsupported Frappe version '{version_text}' for omnexa_experience. "
			"Supported range is >=15.0,<16.0.",
			frappe.ValidationError,
		)


def _ensure_portal_roles():
	roles = (
		("Portal Customer",),
		("Portal Doctor",),
		("Portal Supplier",),
		("Portal Loan Client",),
	)
	for role_name in roles:
		if frappe.db.exists("Role", role_name):
			continue
		doc = frappe.new_doc("Role")
		doc.update({"role_name": role_name, "desk_access": 0, "two_factor_auth": 0})
		doc.insert(ignore_permissions=True)


def _ensure_default_portal_hub():
	if not frappe.db.exists("DocType", "Experience Portal Hub"):
		return
	for company in frappe.get_all("Company", pluck="name", limit=5):
		if frappe.db.exists("Experience Portal Hub", company):
			continue
		branch = frappe.db.get_value("Branch", {"company": company}, "name")
		doc = frappe.new_doc("Experience Portal Hub")
		doc.company = company
		doc.default_branch = branch
		doc.is_enabled = 1
		doc.site_slug = frappe.scrub(company).replace("_", "-")[:60]
		doc.insert(ignore_permissions=True)


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
	_ensure_portal_roles()
	_ensure_default_theme()
	_ensure_default_portal_hub()


def after_migrate():
	_ensure_portal_roles()
	_ensure_default_theme()
	_ensure_default_portal_hub()
