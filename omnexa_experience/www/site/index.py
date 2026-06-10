# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_experience.omnexa_experience.activity_sites import resolve_public_site_url


def get_context(context):
	frappe.local.flags.redirect_location = resolve_public_site_url(
		site=frappe.form_dict.get("site"),
		company=frappe.form_dict.get("company"),
		branch=frappe.form_dict.get("branch"),
	)
