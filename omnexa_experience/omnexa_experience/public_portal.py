# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Unified multi-vertical public portal APIs."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_url

from omnexa_experience.omnexa_experience.portal_adapters import get_sub_portal_dashboard, get_vertical_snapshot
from omnexa_experience.omnexa_experience.portal_registry import (
	list_active_sub_portals,
	list_active_verticals,
	sub_portal_by_id,
	vertical_by_id,
)


def _hub_doc(company: str):
	if not frappe.db.exists("Experience Portal Hub", company):
		return None
	doc = frappe.get_doc("Experience Portal Hub", company)
	if not doc.is_enabled:
		frappe.throw(_("Portal is disabled for this company."))
	return doc


def _default_portal_context() -> dict | None:
	"""Resolve tenant when /portal is opened without ?site= or ?company=."""
	if frappe.db.exists("DocType", "Experience Portal Hub"):
		hubs = frappe.get_all(
			"Experience Portal Hub",
			filters={"is_enabled": 1},
			fields=["company", "default_branch", "site_slug"],
			order_by="modified desc",
			limit=1,
		)
		if hubs:
			row = hubs[0]
			return {
				"company": row.company,
				"branch": row.default_branch or frappe.db.get_value("Branch", {"company": row.company}, "name"),
				"site_slug": row.site_slug,
			}

	company = (
		frappe.defaults.get_global_default("company")
		or frappe.db.get_value("Company", {}, "name", order_by="creation asc")
	)
	if not company:
		return None

	branch = frappe.db.get_value("Branch", {"company": company}, "name", order_by="creation asc")
	site_slug = None
	if frappe.db.exists("DocType", "Experience Portal Hub"):
		site_slug = frappe.db.get_value(
			"Experience Portal Hub",
			{"company": company, "is_enabled": 1},
			"site_slug",
		)
	return {"company": company, "branch": branch, "site_slug": site_slug}


def resolve_portal(*, site: str | None = None, company: str | None = None, branch: str | None = None) -> dict:
	if site:
		row = frappe.db.get_value(
			"Experience Portal Hub",
			{"site_slug": site.strip().lower(), "is_enabled": 1},
			["name", "company", "default_branch"],
			as_dict=True,
		)
		if not row:
			frappe.throw(_("Portal not found or disabled."), frappe.DoesNotExistError)
		return {
			"company": row.company,
			"branch": branch or row.default_branch,
			"site_slug": site.strip().lower(),
		}

	if company:
		if not frappe.db.exists("Company", company):
			frappe.throw(_("Company not found."))
		hub = frappe.db.get_value(
			"Experience Portal Hub",
			{"company": company, "is_enabled": 1},
			["site_slug", "default_branch"],
			as_dict=True,
		)
		return {
			"company": company,
			"branch": branch or (hub.default_branch if hub else frappe.db.get_value("Branch", {"company": company}, "name")),
			"site_slug": hub.site_slug if hub else None,
		}

	ctx = _default_portal_context()
	if ctx:
		if branch:
			ctx["branch"] = branch
		return ctx

	frappe.throw(_("Site slug or company is required."))


def build_portal_urls(*, company: str, site_slug: str | None = None) -> dict:
	q = f"site={site_slug}" if site_slug else f"company={company}"
	suffix = f"?{q}"
	base = get_url("/portal")
	return {
		"home": f"{base}{suffix}",
		"patient": f"{base}/patient{suffix}",
		"customer": f"{base}/customer{suffix}",
		"doctor": f"{base}/doctor{suffix}",
		"supplier": f"{base}/supplier{suffix}",
		"loan": f"{base}/loan{suffix}",
	}


@frappe.whitelist(allow_guest=True)
def get_portal_config(site: str | None = None, company: str | None = None, branch: str | None = None) -> dict:
	ctx = resolve_portal(site=site, company=company, branch=branch)
	company = ctx["company"]
	branch = ctx.get("branch")
	hub = _hub_doc(company)
	if not hub:
		# Fallback config when hub not configured yet
		return {
			"company": company,
			"branch": branch,
			"portal_name_ar": company,
			"portal_name_en": company,
			"tagline_ar": "بوابة موحدة",
			"tagline_en": "Unified portal",
			"primary_color": "#003366",
			"verticals": [],
			"sub_portals": [],
			"urls": build_portal_urls(company=company, site_slug=ctx.get("site_slug")),
			"is_configured": False,
		}

	verticals = list_active_verticals(hub)
	sub_portals = list_active_sub_portals(hub, verticals)
	urls = build_portal_urls(company=company, site_slug=hub.site_slug)

	# Bridge to healthcare hospital site when available
	if branch and "omnexa_healthcare" in frappe.get_installed_apps():
		hospital_slug = frappe.db.get_value("Healthcare Branch Website", {"branch": branch, "is_enabled": 1}, "site_slug")
		if hospital_slug:
			urls["hospital"] = get_url(f"/hospital?site={hospital_slug}")

	return {
		"company": company,
		"branch": branch,
		"site_slug": hub.site_slug,
		"portal_name_ar": hub.portal_name_ar,
		"portal_name_en": hub.portal_name_en,
		"tagline_ar": hub.tagline_ar,
		"tagline_en": hub.tagline_en,
		"logo": hub.portal_logo,
		"primary_color": hub.primary_color or "#003366",
		"contact": {"phone": hub.contact_phone, "email": hub.contact_email},
		"verticals": verticals,
		"sub_portals": sub_portals,
		"urls": urls,
		"is_configured": True,
	}


@frappe.whitelist(allow_guest=True)
def get_vertical_page(site: str | None = None, company: str | None = None, branch: str | None = None, vertical: str | None = None) -> dict:
	if not vertical or not vertical_by_id(vertical):
		frappe.throw(_("Unknown business activity."))
	ctx = resolve_portal(site=site, company=company, branch=branch)
	return get_vertical_snapshot(vertical_id=vertical, company=ctx["company"], branch=ctx.get("branch"))


@frappe.whitelist()
def get_sub_portal_home(
	site: str | None = None,
	company: str | None = None,
	branch: str | None = None,
	sub_portal: str | None = None,
) -> dict:
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required."), frappe.AuthenticationError)
	if not sub_portal or not sub_portal_by_id(sub_portal):
		frappe.throw(_("Unknown sub-portal."))
	ctx = resolve_portal(site=site, company=company, branch=branch)
	return get_sub_portal_dashboard(
		sub_portal=sub_portal,
		company=ctx["company"],
		branch=ctx.get("branch"),
		user=frappe.session.user,
	)


@frappe.whitelist()
def get_portal_urls(company: str) -> dict:
	if not company:
		frappe.throw(_("Company is required"))
	if not frappe.has_permission("Experience Portal Hub", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	slug = frappe.db.get_value("Experience Portal Hub", company, "site_slug")
	urls = build_portal_urls(company=company, site_slug=slug)
	return {"company": company, "site_slug": slug, "public_url": urls["home"], "urls": urls}
