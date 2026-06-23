# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Redirect legacy activity site paths to vertical-app website routes."""

from __future__ import annotations

import frappe

from omnexa_experience.omnexa_experience.activity_website_registry import resolve_legacy_redirect


def before_request_legacy_activity_redirect():
	if not getattr(frappe.local, "request", None):
		return
	if frappe.request.method != "GET":
		return

	path = frappe.request.path or ""
	target = resolve_legacy_redirect(path)
	if not target:
		return

	qs = frappe.request.query_string
	if qs:
		if isinstance(qs, bytes):
			qs = qs.decode()
		target = f"{target}?{qs}"

	frappe.local.flags.redirect_location = target
	raise frappe.Redirect
