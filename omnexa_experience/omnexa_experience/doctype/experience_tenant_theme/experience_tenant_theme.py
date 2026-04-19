# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, now_datetime, validate_url

from omnexa_theme_manager.theme_presets import get_theme_preset

_HEX6 = re.compile(r"^#[0-9A-Fa-f]{6}$")
_FONT_STACK_SAFE = re.compile(r"^[a-zA-Z0-9, \-\.'\"]{1,200}$")
_UNSAFE_URL_CHARS = re.compile(r'["\'\\<>\n\r]')
_MAX_ASSET_URL_LEN = 2048

# WCAG 2.2 §1.4.11 (non-text): minimum ~3:1 for UI components; we enforce 3:1 when both primary colors are set.
_MIN_PRIMARY_CONTRAST_RATIO = 3.0
_THEME_MODE = {"auto", "light", "dark"}
_FONT_SIZES = {"14px", "15px", "16px", "17px", "18px"}
_UI_DENSITY = {"compact", "comfortable", "spacious"}
_RADIUS_SCALE = {"classic", "soft", "rounded"}


def _hex_to_srgb_channels(hex6: str) -> tuple[float, float, float]:
	r = int(hex6[1:3], 16) / 255.0
	g = int(hex6[3:5], 16) / 255.0
	b = int(hex6[5:7], 16) / 255.0
	return r, g, b


def _linearize(channel: float) -> float:
	return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex6: str) -> float:
	r, g, b = _hex_to_srgb_channels(hex6)
	return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)


def _contrast_ratio(fg_hex: str, bg_hex: str) -> float:
	l1 = _relative_luminance(fg_hex)
	l2 = _relative_luminance(bg_hex)
	light, dark = max(l1, l2), min(l1, l2)
	return (light + 0.05) / (dark + 0.05)


def _norm_hex(label: str, value: str | None) -> str | None:
	if not (value or "").strip():
		return None
	v = value.strip()
	if not _HEX6.match(v):
		frappe.throw(_("{0} must be a #RRGGBB hex color.").format(label), title=_("Theme"))
	return v


def _norm_font_stack(value: str | None) -> str | None:
	if not (value or "").strip():
		return None
	v = value.strip()
	if len(v) > 200 or not _FONT_STACK_SAFE.match(v):
		frappe.throw(
			_("Font stack may only contain letters, digits, commas, spaces, hyphens, and quotes (max 200)."),
			title=_("Theme"),
		)
	return v


def _norm_asset_url(label: str, value: str | None) -> str | None:
	if not (value or "").strip():
		return None
	v = value.strip()
	if len(v) > _MAX_ASSET_URL_LEN:
		frappe.throw(
			_("{0} must be at most {1} characters.").format(label, _MAX_ASSET_URL_LEN),
			title=_("Theme"),
		)
	if _UNSAFE_URL_CHARS.search(v):
		frappe.throw(
			_("{0} must not contain quotes, backslashes, angle brackets, or newlines.").format(label),
			title=_("Theme"),
		)
	# Allow relative file URLs (e.g. /files/logo.png) for Attach fields; disallow other schemes.
	if v.startswith("/"):
		return v
	if not validate_url(v, valid_schemes=("https", "http")):
		frappe.throw(_("{0} must be a valid http(s) URL or /files path.").format(label), title=_("Theme"))
	return v


class ExperienceTenantTheme(Document):
	def _apply_preset_defaults(self):
		preset = get_theme_preset(getattr(self, "theme_preset", None))
		for fieldname in (
			"primary_color",
			"primary_contrast",
			"background_color",
			"surface_color",
			"foreground_color",
			"font_stack_for_web",
			"desk_theme_mode",
			"desk_base_font_size",
			"desk_ui_density",
			"desk_radius_scale",
		):
			if not (getattr(self, fieldname, None) or "").strip():
				setattr(self, fieldname, preset.get(fieldname))

	def validate(self):
		self.theme_preset = (self.theme_preset or "erpgenex_theme_0426").strip() or "erpgenex_theme_0426"
		self._apply_preset_defaults()
		self.primary_color = _norm_hex(_("Primary"), self.primary_color)
		self.primary_contrast = _norm_hex(_("Primary contrast"), self.primary_contrast)
		self.background_color = _norm_hex(_("Background"), self.background_color)
		self.surface_color = _norm_hex(_("Surface"), self.surface_color)
		self.foreground_color = _norm_hex(_("Foreground"), self.foreground_color)
		self.font_stack_for_web = _norm_font_stack(self.font_stack_for_web)
		# Attach fields store file URLs as strings; normalize/validate both attach and fallback URL fields.
		self.logo = _norm_asset_url(_("Logo"), self.logo)
		self.logo_url = _norm_asset_url(_("Logo URL"), self.logo_url)
		self.favicon = _norm_asset_url(_("Favicon"), self.favicon)
		self.favicon_url = _norm_asset_url(_("Favicon URL"), self.favicon_url)
		if self.desk_theme_mode not in _THEME_MODE:
			frappe.throw(_("Desk theme mode must be auto, light, or dark."), title=_("Theme"))
		if self.desk_base_font_size not in _FONT_SIZES:
			frappe.throw(_("Desk base font size must be one of {0}.").format(", ".join(sorted(_FONT_SIZES))), title=_("Theme"))
		if self.desk_ui_density not in _UI_DENSITY:
			frappe.throw(_("Desk UI density must be one of {0}.").format(", ".join(sorted(_UI_DENSITY))), title=_("Theme"))
		if self.desk_radius_scale not in _RADIUS_SCALE:
			frappe.throw(_("Desk radius style must be one of {0}.").format(", ".join(sorted(_RADIUS_SCALE))), title=_("Theme"))
		if self.primary_color and self.primary_contrast:
			ratio = _contrast_ratio(self.primary_contrast, self.primary_color)
			if ratio + 1e-9 < _MIN_PRIMARY_CONTRAST_RATIO:
				frappe.throw(
					_(
						"Primary and Primary contrast must reach at least {0}:1 contrast (WCAG non-text baseline). Current: {1:.2f}:1."
					).format(_MIN_PRIMARY_CONTRAST_RATIO, ratio),
					title=_("Theme"),
				)

	def before_save(self):
		if self.apply_to_public_site:
			# Single active theme per site (public bundle).
			frappe.db.sql(
				"""
				update `tabExperience Tenant Theme`
				set apply_to_public_site = 0
				where coalesce(apply_to_public_site, 0) = 1
					and name != %(name)s
				""",
				{"name": self.name or ""},
			)
		if cint(getattr(self, "apply_to_desk", 0)):
			frappe.db.sql(
				"""
				update `tabExperience Tenant Theme`
				set apply_to_desk = 0
				where coalesce(apply_to_desk, 0) = 1
					and company = %(company)s
					and name != %(name)s
				""",
				{"company": self.company, "name": self.name or ""},
			)


def _assert_theme_admin():
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required."), frappe.PermissionError, title=_("Theme"))
	frappe.only_for("System Manager")


def _get_theme_doc(theme: str):
	if not theme or not frappe.db.exists("Experience Tenant Theme", theme):
		frappe.throw(_("Theme not found."), frappe.DoesNotExistError, title=_("Theme"))
	return frappe.get_doc("Experience Tenant Theme", theme)


def _stamp_publish(doc, note: str | None = None):
	doc.published_at = now_datetime()
	doc.published_by = frappe.session.user
	doc.publish_note = (note or "").strip()[:500] or None


def _theme_snapshot(doc) -> dict:
	return {
		"name": doc.name,
		"company": doc.company,
		"theme_preset": doc.theme_preset or "erpgenex_theme_0426",
		"apply_to_public_site": cint(doc.apply_to_public_site) or 0,
		"apply_to_desk": cint(doc.apply_to_desk) or 0,
		"primary_color": doc.primary_color or "",
		"primary_contrast": doc.primary_contrast or "",
		"background_color": doc.background_color or "",
		"surface_color": doc.surface_color or "",
		"foreground_color": doc.foreground_color or "",
		"font_stack_for_web": doc.font_stack_for_web or "",
		"desk_theme_mode": doc.desk_theme_mode or "auto",
		"desk_base_font_size": doc.desk_base_font_size or "16px",
		"desk_ui_density": doc.desk_ui_density or "comfortable",
		"desk_radius_scale": doc.desk_radius_scale or "soft",
		"logo": doc.logo or "",
		"logo_url": doc.logo_url or "",
		"favicon": doc.favicon or "",
		"favicon_url": doc.favicon_url or "",
		"published_at": doc.published_at,
		"published_by": doc.published_by or "",
		"publish_note": doc.publish_note or "",
	}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=30, seconds=60, methods=["POST"])
def publish_theme(theme: str | None = None, company: str | None = None, note: str | None = None):
	"""Publish a theme (set active public theme) and stamp publish metadata."""
	_assert_theme_admin()
	doc = _get_theme_doc(theme)
	if company and doc.company != company:
		frappe.throw(_("Theme does not belong to this company."), title=_("Theme"))
	doc.apply_to_public_site = 1
	_stamp_publish(doc, note=note)
	doc.save(ignore_permissions=True)
	return {"theme": doc.name, "company": doc.company, "published_at": doc.published_at}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=30, seconds=60, methods=["POST"])
def rollback_theme(company: str | None = None, note: str | None = None):
	"""Rollback to last published theme for a company (excluding current active)."""
	_assert_theme_admin()
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("A valid company is required."), title=_("Theme"))
	current = frappe.db.get_value("Experience Tenant Theme", {"company": company, "apply_to_public_site": 1}, "name")
	rows = frappe.get_all(
		"Experience Tenant Theme",
		filters={"company": company, "published_at": ("is", "set")},
		fields=["name", "published_at"],
		order_by="published_at desc",
		limit_page_length=2,
		ignore_permissions=True,
	)
	target = None
	for row in rows:
		if row["name"] != current:
			target = row["name"]
			break
	if not target:
		frappe.throw(_("No previous published theme available for rollback."), title=_("Theme"))
	return publish_theme(theme=target, company=company, note=(note or "rollback"))


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=30, seconds=60, methods=["POST"])
def rollback_theme_to(theme: str | None = None, company: str | None = None, note: str | None = None):
	"""Rollback by explicitly selecting a previously published theme row."""
	_assert_theme_admin()
	doc = _get_theme_doc(theme)
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("A valid company is required."), title=_("Theme"))
	if doc.company != company:
		frappe.throw(_("Theme does not belong to this company."), title=_("Theme"))
	if not doc.published_at:
		frappe.throw(_("Selected theme has never been published."), title=_("Theme"))
	return publish_theme(theme=doc.name, company=company, note=(note or "rollback_to"))


@frappe.whitelist(methods=["GET"])
@rate_limit(limit=60, seconds=60, methods=["GET"])
def list_theme_publish_history(company: str | None = None, limit_page_length: int | str | None = 20):
	"""List latest published theme events for a company."""
	_assert_theme_admin()
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("A valid company is required."), title=_("Theme"))
	page = min(max(cint(limit_page_length) or 20, 1), 100)
	rows = frappe.get_all(
		"Experience Tenant Theme",
		filters={"company": company, "published_at": ("is", "set")},
		fields=["name", "published_at", "published_by", "publish_note", "apply_to_public_site"],
		order_by="published_at desc",
		limit_page_length=page,
		ignore_permissions=True,
	)
	return {"history": rows, "limit_page_length": page}


@frappe.whitelist(methods=["GET"])
@rate_limit(limit=60, seconds=60, methods=["GET"])
def compare_themes(theme_a: str | None = None, theme_b: str | None = None, company: str | None = None):
	"""Compare two theme versions and return field-level differences."""
	_assert_theme_admin()
	doc_a = _get_theme_doc(theme_a or "")
	doc_b = _get_theme_doc(theme_b or "")
	if company:
		if not frappe.db.exists("Company", company):
			frappe.throw(_("A valid company is required."), title=_("Theme"))
		if doc_a.company != company or doc_b.company != company:
			frappe.throw(_("Both themes must belong to the requested company."), title=_("Theme"))
	if doc_a.company != doc_b.company:
		frappe.throw(_("Themes must belong to the same company."), title=_("Theme"))

	snap_a = _theme_snapshot(doc_a)
	snap_b = _theme_snapshot(doc_b)
	keys = [
		"apply_to_public_site",
		"apply_to_desk",
		"theme_preset",
		"primary_color",
		"primary_contrast",
		"background_color",
		"surface_color",
		"foreground_color",
		"font_stack_for_web",
		"desk_theme_mode",
		"desk_base_font_size",
		"desk_ui_density",
		"desk_radius_scale",
		"logo",
		"logo_url",
		"favicon",
		"favicon_url",
		"published_at",
		"published_by",
		"publish_note",
	]
	diffs = []
	for k in keys:
		if (snap_a.get(k) or "") != (snap_b.get(k) or ""):
			diffs.append({"field": k, "a": snap_a.get(k), "b": snap_b.get(k)})
	return {
		"theme_a": snap_a,
		"theme_b": snap_b,
		"diff_count": len(diffs),
		"diffs": diffs,
	}


_JSON_IMPORT_FIELDS = (
	"company",
	"theme_preset",
	"apply_to_public_site",
	"apply_to_desk",
	"primary_color",
	"primary_contrast",
	"background_color",
	"surface_color",
	"foreground_color",
	"font_stack_for_web",
	"desk_theme_mode",
	"desk_base_font_size",
	"desk_ui_density",
	"desk_radius_scale",
	"logo",
	"logo_url",
	"favicon",
	"favicon_url",
)


def _apply_theme_payload(doc: Document, data: dict) -> None:
	for k in _JSON_IMPORT_FIELDS:
		if k not in data:
			continue
		val = data.get(k)
		if val is None:
			continue
		if k in ("apply_to_public_site", "apply_to_desk"):
			setattr(doc, k, cint(val))
		else:
			setattr(doc, k, val)


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=30, seconds=60, methods=["POST"])
def activate_desk_theme(theme: str | None = None):
	"""Set this row as the active Desk theme for its company."""
	_assert_theme_admin()
	doc = _get_theme_doc(theme)
	doc.apply_to_desk = 1
	doc.save(ignore_permissions=True)
	return {"ok": True, "name": doc.name, "company": doc.company}


@frappe.whitelist(methods=["GET"])
@rate_limit(limit=60, seconds=60, methods=["GET"])
def export_theme_json(theme: str | None = None):
	"""Export a snapshot suitable for backup / import."""
	_assert_theme_admin()
	doc = _get_theme_doc(theme)
	return {"ok": True, "snapshot": _theme_snapshot(doc)}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=20, seconds=60, methods=["POST"])
def import_theme_json(theme: str | None = None, payload: str | dict | None = None):
	"""Create or update a theme from JSON (export_theme_json snapshot or a subset of fields)."""
	_assert_theme_admin()
	if payload is None:
		frappe.throw(_("Payload required."), title=_("Theme"))
	data = frappe.parse_json(payload) if isinstance(payload, str) else payload
	if not isinstance(data, dict):
		frappe.throw(_("Payload must be a JSON object."), title=_("Theme"))
	if theme:
		doc = _get_theme_doc(theme)
		_apply_theme_payload(doc, data)
		doc.save(ignore_permissions=True)
		return {"ok": True, "name": doc.name}
	company = data.get("company")
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Payload must include a valid company for new themes."), title=_("Theme"))
	doc = frappe.new_doc("Experience Tenant Theme")
	_apply_theme_payload(doc, data)
	doc.insert(ignore_permissions=True)
	return {"ok": True, "name": doc.name}
