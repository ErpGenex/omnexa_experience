# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Registry of vertical-app public website packs keyed by Company business activity."""

from __future__ import annotations

import frappe


def get_activity_website_packs() -> dict[str, dict]:
	"""Return {business_activity: pack} from installed apps' hooks."""
	packs: dict[str, dict] = {}
	for entry in frappe.get_hooks("activity_website_packs") or []:
		if isinstance(entry, dict):
			activity = entry.get("business_activity")
			if activity:
				packs[activity] = entry
	return packs


def get_activity_website_pack(activity: str | None) -> dict | None:
	if not activity:
		return None
	return get_activity_website_packs().get(activity)


def activity_site_path_for(activity: str) -> str | None:
	pack = get_activity_website_pack(activity)
	if pack and pack.get("base_path"):
		return pack["base_path"]
	return None


def activity_nav_for(activity: str) -> list[dict] | None:
	pack = get_activity_website_pack(activity)
	nav = pack.get("nav") if pack else None
	return nav if nav else None


def get_seed_demo_callable(activity: str) -> str | None:
	pack = get_activity_website_pack(activity)
	if not pack:
		return None
	return pack.get("seed_demo_method") or pack.get("seed_demo_api")


def resolve_legacy_redirect(path: str) -> str | None:
	"""Map legacy experience paths (e.g. /campus) to app-specific website paths."""
	if not path:
		return None
	normalized = path.rstrip("/") or path
	for pack in get_activity_website_packs().values():
		legacy_base = pack.get("legacy_base_path")
		new_base = pack.get("base_path")
		if not legacy_base or not new_base:
			continue
		legacy_base = legacy_base.rstrip("/") or legacy_base
		new_base = new_base.rstrip("/") or new_base
		if normalized == legacy_base:
			return new_base
		if normalized.startswith(legacy_base + "/"):
			return new_base + normalized[len(legacy_base) :]
	return None


def list_installed_activity_websites() -> list[dict]:
	"""Summary for desk / diagnostics."""
	out: list[dict] = []
	for activity, pack in sorted(get_activity_website_packs().items()):
		out.append(
			{
				"business_activity": activity,
				"app": pack.get("app"),
				"base_path": pack.get("base_path"),
				"legacy_base_path": pack.get("legacy_base_path"),
				"has_seed": bool(get_seed_demo_callable(activity)),
			}
		)
	return out


@frappe.whitelist()
def get_installed_activity_websites_api() -> list[dict]:
	return list_installed_activity_websites()
