# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Company-level demo seed for public activity websites (scoped by Business Activity)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, get_url

from omnexa_experience.omnexa_experience.activity_sites import (
	activity_site_path,
	build_activity_site_url,
	default_hero_image,
)
from omnexa_experience.omnexa_experience.portal_registry import activity_profile, get_company_business_activity

DEMO_MARKER = "DEMO-ACT-"

CATALOG_BY_ACTIVITY: dict[str, list[tuple[str, str, str, str]]] = {
	"Trading": [
		("smart-watch", "Smart Watch Pro", "ساعة ذكية برو", "product"),
		("laptop-ultra", "Ultra Laptop 15", "لابتوب ألترا 15", "product"),
		("home-bundle", "Home Essentials Bundle", "باقة أساسيات المنزل", "product"),
		("fashion-set", "Premium Fashion Set", "طقم أزياء فاخر", "product"),
		("grocery-box", "Weekly Grocery Box", "صندوق بقالة أسبوعي", "product"),
		("kids-toys", "Kids Learning Toys", "ألعاب تعليمية للأطفال", "product"),
	],
	"Manufacturing": [
		("industrial-pump", "Industrial Water Pump", "مضخة مياه صناعية", "product"),
		("cnc-part", "CNC Machined Part", "قطعة ميكانيكية CNC", "product"),
		("maintenance-kit", "Maintenance Service Kit", "طقم صيانة", "service"),
		("spare-motor", "Spare Motor Unit", "وحدة محرك احتياطية", "product"),
	],
	"Agriculture": [
		("organic-dates", "Organic Dates 5kg", "تمر عضوي 5 كجم", "product"),
		("fresh-vegetables", "Fresh Vegetable Crate", "صندوق خضروات طازجة", "product"),
		("farm-consult", "Farm Advisory Visit", "زيارة استشارية زراعية", "service"),
	],
	"Services": [
		("audit-pack", "Business Audit Package", "باقة تدقيق أعمال", "service"),
		("it-support", "IT Support Retainer", "عقد دعم تقني", "service"),
		("legal-review", "Legal Document Review", "مراجعة قانونية", "service"),
	],
	"Statutory Audit": [
		("statutory-audit", "Statutory Audit Engagement", "تدقيق قانوني", "service"),
		("tax-filing", "Corporate Tax Filing", "إقرار ضريبي", "service"),
	],
	"Financial Services": [
		("personal-loan", "Personal Finance Product", "تمويل شخصي", "service"),
		("sme-loan", "SME Working Capital", "تمويل رأس مال عامل", "service"),
		("auto-finance", "Auto Finance Plan", "تمويل سيارات", "service"),
	],
	"Bakeries": [
		("sourdough", "Artisan Sourdough Loaf", "خبز سourdough حرفي", "product"),
		("pastry-box", "Pastry Assortment Box", "صندوق معجنات", "product"),
		("catering", "Event Catering Package", "باقة تموين مناسبات", "service"),
	],
	"Construction": [
		("villa-package", "Villa Construction Package", "باقة بناء فيلا", "service"),
		("renovation", "Commercial Renovation", "تجديد تجاري", "service"),
	],
	"Engineering Consulting": [
		("structural-review", "Structural Design Review", "مراجعة إنشائية", "service"),
		("mep-design", "MEP Design Package", "تصميم MEP", "service"),
	],
	"General": [
		("starter-service", "Starter Service Package", "باقة خدمات أساسية", "service"),
		("starter-product", "Starter Product Bundle", "باقة منتجات أساسية", "product"),
	],
}

EDUCATION_PROGRAMS: list[tuple[str, str, str]] = [
	("CS-BSC", "Computer Science BSc", "Bachelor"),
	("BA-MBA", "Business Administration MBA", "Master"),
	("ENG-DIP", "Engineering Diploma", "Diploma"),
	("MED-PREP", "Medical Foundation Program", "Certificate"),
]

TOURISM_ROOMS: list[tuple[str, str, float]] = [
	("STD", "Standard Room", 450.0),
	("DLX", "Deluxe Sea View", 750.0),
	("STE", "Executive Suite", 1200.0),
	("FAM", "Family Suite", 980.0),
]


def _assert_system_manager() -> None:
	if "System Manager" not in (frappe.get_roles() or []) and frappe.session.user != "Administrator":
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _resolve_branch(company: str, branch: str | None) -> str:
	if branch and frappe.db.exists("Branch", branch):
		if frappe.db.get_value("Branch", branch, "company") != company:
			frappe.throw(_("Branch does not belong to company."))
		return branch
	head = frappe.db.get_value("Branch", {"company": company, "is_head_office": 1}, "name")
	if head:
		return head
	any_branch = frappe.db.get_value("Branch", {"company": company}, "name", order_by="creation asc")
	if not any_branch:
		frappe.throw(_("Create at least one branch for this company first."))
	return any_branch


def _hub_branding(activity: str, company: str) -> dict:
	profile = activity_profile(activity)
	company_name = frappe.db.get_value("Company", company, "company_name") or company
	return {
		"portal_name_ar": company_name,
		"portal_name_en": company_name,
		"tagline_ar": profile.get("tagline_ar"),
		"tagline_en": profile.get("tagline_en"),
		"primary_color": profile.get("accent") or "#003366",
		"hero_image": default_hero_image(activity),
		"contact_phone": "+966 50 000 0000",
		"contact_email": "info@example.com",
		"follow_company_activity": 1,
	}


def _ensure_portal_hub(company: str, branch: str, activity: str) -> frappe.Document:
	if not frappe.db.exists("DocType", "Experience Portal Hub"):
		frappe.throw(_("Install and migrate omnexa_experience first."))
	branding = _hub_branding(activity, company)
	slug = frappe.scrub(company).replace("_", "-")[:60]
	if frappe.db.exists("Experience Portal Hub", company):
		doc = frappe.get_doc("Experience Portal Hub", company)
		doc.update(
			{
				"is_enabled": 1,
				"default_branch": branch,
				"site_slug": doc.site_slug or slug,
				**branding,
			}
		)
		doc.save(ignore_permissions=True)
		return doc

	doc = frappe.get_doc(
		{
			"doctype": "Experience Portal Hub",
			"company": company,
			"default_branch": branch,
			"is_enabled": 1,
			"site_slug": slug,
			**branding,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def _upsert_catalog_item(
	company: str,
	activity: str,
	slug: str,
	title_en: str,
	title_ar: str,
	item_type: str,
) -> str:
	marker_slug = f"{DEMO_MARKER}{slug}".lower()
	existing = frappe.db.get_value("Catalog Item", {"company": company, "slug": marker_slug}, "name")
	if existing:
		frappe.db.set_value(
			"Catalog Item",
			existing,
			{"published": 1, "title_en": title_en, "title_ar": title_ar, "item_type": item_type},
			update_modified=False,
		)
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Catalog Item",
			"company": company,
			"commerce_segment": activity,
			"slug": marker_slug,
			"title_en": f"{DEMO_MARKER} {title_en}",
			"title_ar": title_ar,
			"item_type": item_type,
			"published": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _seed_catalog_demo(company: str, activity: str) -> dict:
	if not frappe.db.exists("DocType", "Catalog Item"):
		return {"skipped": True, "reason": "Catalog Item DocType missing"}
	rows = CATALOG_BY_ACTIVITY.get(activity) or CATALOG_BY_ACTIVITY.get("General", [])
	created: list[str] = []
	for slug, title_en, title_ar, item_type in rows:
		created.append(_upsert_catalog_item(company, activity, slug, title_en, title_ar, item_type))
	return {"catalog_items": created, "count": len(created)}


def _seed_education_demo(company: str, branch: str, force: int) -> dict:
	if "omnexa_education" not in (frappe.get_installed_apps() or []):
		return {"skipped": True, "reason": "omnexa_education not installed"}
	if not frappe.db.exists("DocType", "Education Institution"):
		return {"skipped": True}

	code = f"{DEMO_MARKER}MAIN"
	inst_name = f"{company}-{code}"
	if frappe.db.exists("Education Institution", inst_name):
		institution = inst_name
	elif force:
		institution = inst_name
	else:
		institution = frappe.db.get_value("Education Institution", {"company": company}, "name")
		if institution:
			return {"institution": institution, "message": "already_exists"}

	if not frappe.db.exists("Education Institution", inst_name):
		frappe.get_doc(
			{
				"doctype": "Education Institution",
				"institution_code": code,
				"institution_name": f"{DEMO_MARKER} ErpGenEx Academy",
				"company": company,
				"institution_type": "University",
				"status": "Active",
				"website": f"https://campus.example/{frappe.scrub(company)}",
			}
		).insert(ignore_permissions=True)
		institution = inst_name

	programs: list[str] = []
	if frappe.db.exists("DocType", "Education Program"):
		for prog_code, prog_name, level in EDUCATION_PROGRAMS:
			full_code = f"{DEMO_MARKER}{prog_code}"
			if frappe.db.exists("Education Program", full_code):
				programs.append(full_code)
				continue
			frappe.get_doc(
				{
					"doctype": "Education Program",
					"program_code": full_code,
					"program_name": f"{DEMO_MARKER} {prog_name}",
					"institution": institution,
					"company": company,
					"branch": branch,
					"degree_level": level,
					"is_active": 1,
				}
			).insert(ignore_permissions=True)
			programs.append(full_code)

	return {"institution": institution, "programs": programs}


def _seed_tourism_demo(company: str, branch: str) -> dict:
	out: dict = {}
	if "omnexa_tourism" not in (frappe.get_installed_apps() or []):
		return {"skipped": True, "reason": "omnexa_tourism not installed"}

	room_types: list[str] = []
	if frappe.db.exists("DocType", "Tourism Room Type"):
		for code, name, rate in TOURISM_ROOMS:
			type_code = f"{DEMO_MARKER}{code}"
			existing = frappe.db.get_value(
				"Tourism Room Type", {"company": company, "branch": branch, "type_code": type_code}, "name"
			)
			if existing:
				room_types.append(existing)
				continue
			doc = frappe.get_doc(
				{
					"doctype": "Tourism Room Type",
					"type_code": type_code,
					"type_name": f"{DEMO_MARKER} {name}",
					"company": company,
					"branch": branch,
					"rack_rate": rate,
					"max_occupancy": 2,
					"status": "Active",
				}
			)
			doc.insert(ignore_permissions=True)
			room_types.append(doc.name)

		if frappe.db.exists("DocType", "Tourism Room Unit"):
			for idx, rt in enumerate(room_types[:4], start=1):
				unit_code = f"{DEMO_MARKER}R{idx:02d}"
				existing_unit = frappe.db.get_value(
					"Tourism Room Unit",
					{"company": company, "branch": branch, "unit_code": unit_code},
					"name",
				)
				if existing_unit:
					continue
				frappe.get_doc(
					{
						"doctype": "Tourism Room Unit",
						"unit_code": unit_code,
						"unit_name": f"{DEMO_MARKER} Room {idx}",
						"company": company,
						"branch": branch,
						"room_type": rt,
						"capacity": 2,
						"status": "Available",
					}
				).insert(ignore_permissions=True)

	out["room_types"] = room_types
	# Also expose on activity catalog for /stay site cards
	out["catalog"] = _seed_catalog_demo(company, "Tourism")
	return out


def _seed_healthcare_demo(company: str, branch: str, patients: int, force: int) -> dict:
	if "omnexa_healthcare" not in (frappe.get_installed_apps() or []):
		frappe.throw(_("Install and migrate omnexa_healthcare for Healthcare activity demo."))
	from omnexa_healthcare.utils.branch_demo_seed import seed_healthcare_hospital_demo

	result = seed_healthcare_hospital_demo(
		company=company,
		branch=branch,
		patients=patients,
		force=force,
		include_financial=1,
	)
	# Ensure hero image on branch website for professional homepage
	if frappe.db.exists("Healthcare Branch Website", branch):
		frappe.db.set_value(
			"Healthcare Branch Website",
			branch,
			{"hero_image": default_hero_image("Healthcare")},
			update_modified=False,
		)
	slug = frappe.db.get_value("Healthcare Branch Website", branch, "site_slug")
	if slug:
		result["hospital_site_url"] = get_url(f"/hospital?site={slug}")
		result["site_url"] = result["hospital_site_url"]
	return result


def _seed_construction_demo(company: str, branch: str) -> dict:
	if "omnexa_construction" not in (frappe.get_installed_apps() or []):
		return {"skipped": True}
	try:
		from omnexa_construction.utils.demo_seed import seed_construction_portfolio_demo

		return seed_construction_portfolio_demo(company, branch=branch, force=0)
	except Exception as exc:
		return {"skipped": True, "error": str(exc)}


@frappe.whitelist()
def seed_company_activity_website(
	company: str,
	branch: str | None = None,
	force: int | str | None = 0,
	patients: int | str | None = 20,
) -> dict:
	"""Seed a complete public activity website demo from Company settings."""
	_assert_system_manager()
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Company is required"))

	branch = _resolve_branch(company, branch)
	activity = get_company_business_activity(company)
	force_i = cint(force)
	patients_i = max(5, min(50, cint(patients) or 20))

	hub = _ensure_portal_hub(company, branch, activity)
	result: dict = {
		"ok": True,
		"company": company,
		"branch": branch,
		"business_activity": activity,
		"portal_hub": hub.name,
		"site_slug": hub.site_slug,
		"base_path": activity_site_path(activity),
	}

	if activity == "Healthcare":
		result["healthcare"] = _seed_healthcare_demo(company, branch, patients_i, force_i)
		result["site_url"] = result["healthcare"].get("site_url") or result["healthcare"].get("hospital_site_url")
	elif activity == "Education":
		result["education"] = _seed_education_demo(company, branch, force_i)
		result["catalog"] = _seed_catalog_demo(company, activity)
	elif activity in ("Tourism", "Hotel Assets"):
		result["tourism"] = _seed_tourism_demo(company, branch)
	elif activity == "Construction":
		result["construction"] = _seed_construction_demo(company, branch)
		result["catalog"] = _seed_catalog_demo(company, activity)
	else:
		result["catalog"] = _seed_catalog_demo(company, activity)

	if not result.get("site_url"):
		result["site_url"] = build_activity_site_url(
			company=company,
			activity=activity,
			branch=branch,
			site_slug=hub.site_slug,
		)

	result["portal_url"] = get_url(f"/portal?site={hub.site_slug}")
	result["message"] = _("Activity website demo seeded for {0} ({1})").format(activity, company)
	return result
