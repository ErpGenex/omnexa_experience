# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Import Commerce dashboard charts / script reports and heal the Commerce workspace."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.modules.import_file import import_file_by_path

from omnexa_core.workspace_link_prune import prune_workspace_stale_links

_APP_ROOT = Path(__file__).resolve().parent

COMMERCE_REPORTS = (
	"commerce_order_to_cash_pipeline",
	"commerce_booking_pipeline",
	"commerce_payment_outcomes",
	"commerce_revenue_disaggregation",
	"commerce_order_cycle_time",
	"commerce_web_order_line_mix",
	"commerce_booking_service_hours",
)

COMMERCE_CHARTS = (
	"commerce_web_order_mix",
	"commerce_booking_mix",
)


def _import_json(relative_parts: tuple[str, ...]) -> None:
	path = _APP_ROOT.joinpath(*relative_parts)
	if not path.is_file():
		return
	import_file_by_path(str(path), force=True, ignore_version=True)


def ensure_commerce_reports() -> list[str]:
	"""Import standard Commerce script reports from app module files."""
	if not frappe.db.exists("DocType", "Web Order"):
		return []
	imported: list[str] = []
	for slug in COMMERCE_REPORTS:
		_import_json(("report", slug, f"{slug}.json"))
		for name in COMMERCE_REPORT_DISPLAY_NAMES.get(slug, ()):
			if frappe.db.exists("Report", name):
				imported.append(name)
				break
	return sorted(set(imported))


COMMERCE_REPORT_DISPLAY_NAMES: dict[str, tuple[str, ...]] = {
	"commerce_order_to_cash_pipeline": ("Commerce Order-to-Cash Pipeline",),
	"commerce_booking_pipeline": ("Commerce Booking Pipeline",),
	"commerce_payment_outcomes": ("Commerce Payment Outcomes",),
	"commerce_revenue_disaggregation": ("Commerce Revenue Disaggregation",),
	"commerce_order_cycle_time": ("Commerce Order Cycle Time",),
	"commerce_web_order_line_mix": ("Commerce Web Order Line Mix",),
	"commerce_booking_service_hours": ("Commerce Booking Service Hours",),
}


def ensure_commerce_dashboard_charts() -> list[str]:
	if not frappe.db.exists("DocType", "Web Order"):
		return []
	out: list[str] = []
	for slug in COMMERCE_CHARTS:
		_import_json(("dashboard_chart", slug, f"{slug}.json"))
		fallback = {
			"commerce_web_order_mix": "Commerce · Web Order Mix",
			"commerce_booking_mix": "Commerce · Booking Mix",
		}.get(slug)
		if fallback and frappe.db.exists("Dashboard Chart", fallback):
			out.append(fallback)
	return out


def sync_commerce_workspace() -> dict:
	"""Ensure Commerce artifacts exist, then prune/save the workspace."""
	if not frappe.db.exists("Workspace", "Commerce"):
		return {"ok": False, "message": "commerce_workspace_missing"}

	reports = ensure_commerce_reports()
	charts = ensure_commerce_dashboard_charts()

	ws = frappe.get_doc("Workspace", "Commerce")
	prune_workspace_stale_links(ws)
	ws.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": True, "reports": reports, "charts": charts}


@frappe.whitelist()
def sync_commerce_workspace_now():
	frappe.only_for("System Manager")
	return sync_commerce_workspace()
