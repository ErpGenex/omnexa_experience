# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Public API pack for activity-specific marketing websites."""

from __future__ import annotations

import frappe

from omnexa_experience.omnexa_experience.activity_demo_assets import activity_testimonials, premium_hero_image
from omnexa_experience.omnexa_experience.activity_sites import (
	activity_features,
	activity_nav,
	activity_site_path,
	activity_stats,
	default_hero_image,
	service_cards,
	vertical_id_for_activity,
)
from omnexa_experience.omnexa_experience.portal_adapters import get_vertical_snapshot
from omnexa_experience.omnexa_experience.portal_registry import activity_profile, get_company_business_activity
from omnexa_experience.omnexa_experience.public_portal import resolve_portal


def _hub_branding(company: str) -> dict:
	if not frappe.db.exists("Experience Portal Hub", company):
		return {}
	hub = frappe.get_doc("Experience Portal Hub", company)
	if not hub.is_enabled:
		return {}
	return {
		"name_ar": hub.portal_name_ar,
		"name_en": hub.portal_name_en,
		"tagline_ar": hub.tagline_ar,
		"tagline_en": hub.tagline_en,
		"logo": hub.portal_logo,
		"primary_color": hub.primary_color,
		"hero_image": getattr(hub, "hero_image", None),
		"contact_phone": hub.contact_phone,
		"contact_email": hub.contact_email,
		"site_slug": hub.site_slug,
	}


@frappe.whitelist(allow_guest=True)
def get_activity_site_pack_api(
	site: str | None = None,
	company: str | None = None,
	branch: str | None = None,
) -> dict:
	ctx = resolve_portal(site=site, company=company, branch=branch)
	company = ctx["company"]
	branch = ctx.get("branch")
	activity = get_company_business_activity(company)
	profile = activity_profile(activity)
	hub = _hub_branding(company)
	vertical_id = vertical_id_for_activity(activity)
	snapshot = get_vertical_snapshot(vertical_id=vertical_id, company=company, branch=branch)
	items = snapshot.get("items") or []

	base_path = activity_site_path(activity)
	nav = activity_nav(activity)
	for row in nav:
		row = dict(row)
		row["href"] = row.get("href", base_path)

	products = []
	programs = []
	loan_products = []
	for item in items:
		if item.get("institution_name") or item.get("program_name"):
			programs.append(item)
		elif item.get("product_name") or item.get("loan_product"):
			loan_products.append(item)
		else:
			products.append(item)

	return {
		"company": company,
		"branch": branch,
		"site_slug": ctx.get("site_slug") or hub.get("site_slug"),
		"business_activity": activity,
		"vertical": vertical_id,
		"base_path": base_path,
		"name_ar": hub.get("name_ar") or company,
		"name_en": hub.get("name_en") or company,
		"tagline_ar": hub.get("tagline_ar") or profile.get("tagline_ar"),
		"tagline_en": hub.get("tagline_en") or profile.get("tagline_en"),
		"hero_text_ar": profile.get("hero_ar"),
		"hero_text_en": profile.get("hero_en"),
		"hero_image": hub.get("hero_image") or premium_hero_image(activity) or default_hero_image(activity),
		"logo": hub.get("logo"),
		"primary_color": hub.get("primary_color") or profile.get("accent") or "#003366",
		"contact": {
			"phone": hub.get("contact_phone"),
			"email": hub.get("contact_email"),
		},
		"nav": nav,
		"features": activity_features(activity),
		"stats": activity_stats(activity),
		"service_cards": service_cards(activity),
		"testimonials": activity_testimonials(activity),
		"products": products,
		"programs": programs,
		"loan_products": loan_products,
		"actions": snapshot.get("actions") or [],
	}
