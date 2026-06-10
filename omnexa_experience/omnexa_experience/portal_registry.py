# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Registry of business verticals and sub-portals — scoped by Company business activity."""

from __future__ import annotations

from dataclasses import dataclass

import frappe

try:
	from omnexa_core.omnexa_core.app_visibility import _normalize_company_activity
except Exception:
	def _normalize_company_activity(raw: str | None) -> str:
		if not raw or not str(raw).strip():
			return "General"
		return str(raw).split("(")[0].strip() or "General"


@dataclass(frozen=True)
class VerticalDef:
	id: str
	app: str
	hub_field: str
	icon: str
	name_ar: str
	name_en: str
	route: str
	sub_portals: tuple[str, ...]
	company_activities: tuple[str, ...]


@dataclass(frozen=True)
class SubPortalDef:
	id: str
	hub_field: str
	icon: str
	name_ar: str
	name_en: str
	route: str
	roles: tuple[str, ...]
	verticals: tuple[str, ...]


# Company.business_activity → primary public-site vertical
COMPANY_ACTIVITY_PRIMARY_VERTICAL: dict[str, str] = {
	"General": "",
	"Healthcare": "healthcare",
	"Education": "education",
	"Construction": "construction",
	"Engineering Consulting": "engineering",
	"Financial Services": "finance",
	"Trading": "trading",
	"Manufacturing": "manufacturing",
	"Agriculture": "agriculture",
	"Tourism": "tourism",
	"Hotel Assets": "property",
	"Bakeries": "restaurant",
	"Services": "services",
	"Statutory Audit": "services",
}

ACTIVITY_PROFILES: dict[str, dict] = {
	"Healthcare": {
		"tagline_ar": "رعايتكم... أولويتنا",
		"tagline_en": "Your care... our priority",
		"hero_ar": "مستشفى وعيادات متكاملة — احجز موعدك واطّلع على خدماتنا الطبية.",
		"hero_en": "Integrated hospital and clinics — book appointments and explore our medical services.",
		"accent": "#003366",
	},
	"Education": {
		"tagline_ar": "نبني مستقبلاً أفضل بالتعليم",
		"tagline_en": "Building a better future through education",
		"hero_ar": "مؤسسة تعليمية رائدة — التقديم والقبول والخدمات الطلابية.",
		"hero_en": "Leading educational institution — admissions and student services.",
		"accent": "#1a5276",
	},
	"Trading": {
		"tagline_ar": "تسوق بثقة وجودة",
		"tagline_en": "Shop with confidence and quality",
		"hero_ar": "متجرك الإلكتروني — منتجات مختارة وخدمة توصيل سريعة.",
		"hero_en": "Your online store — curated products and fast service.",
		"accent": "#0d47a1",
	},
	"Manufacturing": {
		"tagline_ar": "صناعة بمعايير عالمية",
		"tagline_en": "Manufacturing to global standards",
		"hero_ar": "حلول صناعية متكاملة — منتجات وخدمات ما بعد البيع.",
		"hero_en": "Integrated industrial solutions — products and after-sales services.",
		"accent": "#37474f",
	},
	"Financial Services": {
		"tagline_ar": "شريكك في التمويل",
		"tagline_en": "Your financing partner",
		"hero_ar": "خدمات مالية وتمويلية — تقدم بطلبك وتابع حسابك.",
		"hero_en": "Financial and lending services — apply and track your account.",
		"accent": "#1b4332",
	},
	"Tourism": {
		"tagline_ar": "ضيافة واستقبال راقٍ",
		"tagline_en": "Premium hospitality",
		"hero_ar": "احجز إقامتك واستمتع بتجربة سياحية مميزة.",
		"hero_en": "Book your stay and enjoy a distinguished travel experience.",
		"accent": "#00695c",
	},
	"Services": {
		"tagline_ar": "خدمات احترافية بجودة عالية",
		"tagline_en": "Professional services, delivered with excellence",
		"hero_ar": "نقدم حلولاً متخصصة تلبي احتياجات عملائنا.",
		"hero_en": "Specialized solutions tailored to our clients' needs.",
		"accent": "#283593",
	},
	"Construction": {
		"tagline_ar": "نبني بثقة وجودة",
		"tagline_en": "Building with trust and quality",
		"hero_ar": "مشاريع مقاولات وإنشاءات — جودة وتسليم في الموعد.",
		"hero_en": "Construction projects — quality delivery on schedule.",
		"accent": "#e65100",
	},
	"Engineering Consulting": {
		"tagline_ar": "هندسة واستشارات متخصصة",
		"tagline_en": "Specialized engineering consulting",
		"hero_ar": "حلول هندسية احترافية لمشاريعكم.",
		"hero_en": "Professional engineering solutions for your projects.",
		"accent": "#455a64",
	},
	"Agriculture": {
		"tagline_ar": "من الأرض إلى السوق",
		"tagline_en": "From farm to market",
		"hero_ar": "منتجات زراعية وخدمات مزارع بجودة عالية.",
		"hero_en": "Quality agricultural products and farm services.",
		"accent": "#33691e",
	},
	"Hotel Assets": {
		"tagline_ar": "إدارة أصول ضيافة راقية",
		"tagline_en": "Premium hospitality asset management",
		"hero_ar": "خدمات عقارية وضيافة للمستثمرين والعملاء.",
		"hero_en": "Property and hospitality services for investors and guests.",
		"accent": "#004d40",
	},
	"Bakeries": {
		"tagline_ar": "طازج كل يوم",
		"tagline_en": "Fresh every day",
		"hero_ar": "مخبوزات ومنتجات طازجة — اطلب الآن.",
		"hero_en": "Fresh bakery products — order now.",
		"accent": "#bf360c",
	},
	"General": {
		"tagline_ar": "بوابة خدمات عملائنا",
		"tagline_en": "Your customer service portal",
		"hero_ar": "تابع طلباتك وخدماتك من مكان واحد.",
		"hero_en": "Track your orders and services in one place.",
		"accent": "#003366",
	},
}

VERTICALS: tuple[VerticalDef, ...] = (
	VerticalDef("healthcare", "omnexa_healthcare", "enable_healthcare", "🏥", "الصحة والعيادات", "Healthcare", "/portal/vertical/healthcare", ("patient", "doctor"), ("Healthcare",)),
	VerticalDef("trading", "omnexa_trading", "enable_trading", "🛒", "التجارة", "Trading & Commerce", "/portal/vertical/trading", ("customer", "supplier"), ("Trading",)),
	VerticalDef("manufacturing", "omnexa_manufacturing", "enable_manufacturing", "🏭", "التصنيع", "Manufacturing", "/portal/vertical/manufacturing", ("customer", "supplier"), ("Manufacturing",)),
	VerticalDef("services", "omnexa_services", "enable_services", "🔧", "الخدمات", "Professional Services", "/portal/vertical/services", ("customer",), ("Services", "Statutory Audit", "General")),
	VerticalDef("car_rental", "omnexa_car_rental", "enable_car_rental", "🚗", "تأجير السيارات", "Car Rental", "/portal/vertical/car-rental", ("customer",), ("Tourism",)),
	VerticalDef("education", "omnexa_education", "enable_education", "🎓", "التعليم", "Education", "/portal/vertical/education", ("customer",), ("Education",)),
	VerticalDef("finance", "omnexa_consumer_finance", "enable_finance", "🏦", "التمويل والبنوك", "Finance & Banking", "/portal/vertical/finance", ("loan", "customer"), ("Financial Services",)),
	VerticalDef("leasing", "omnexa_leasing_finance", "enable_leasing", "📋", "الإيجار التمويلي", "Leasing", "/portal/vertical/leasing", ("loan", "customer"), ("Financial Services",)),
	VerticalDef("tourism", "omnexa_tourism", "enable_tourism", "🏨", "السياحة والضيافة", "Tourism", "/portal/vertical/tourism", ("customer",), ("Tourism", "Hotel Assets")),
	VerticalDef("restaurant", "omnexa_restaurant", "enable_restaurant", "🍽️", "المطاعم", "Restaurant", "/portal/vertical/restaurant", ("customer",), ("Bakeries",)),
	VerticalDef("property", "erpgenex_property_mgmt", "enable_property", "🏢", "العقارات", "Property", "/portal/vertical/property", ("customer",), ("Hotel Assets",)),
	VerticalDef("agriculture", "omnexa_agriculture", "enable_agriculture", "🌾", "الزراعة", "Agriculture", "/portal/vertical/agriculture", ("customer", "supplier"), ("Agriculture",)),
	VerticalDef("engineering", "omnexa_engineering_consulting", "enable_engineering", "📐", "الاستشارات الهندسية", "Engineering", "/portal/vertical/engineering", ("customer",), ("Engineering Consulting",)),
	VerticalDef("construction", "omnexa_construction", "enable_engineering", "🏗️", "المقاولات", "Construction", "/portal/vertical/construction", ("customer", "supplier"), ("Construction",)),
)

SUB_PORTALS: tuple[SubPortalDef, ...] = (
	SubPortalDef("patient", "enable_patient_portal", "🩺", "بوابة المرضى", "Patients", "/portal/patient", ("Patient Portal User", "Customer"), ("healthcare",)),
	SubPortalDef("customer", "enable_customer_portal", "👤", "بوابة العملاء", "Customers", "/portal/customer", ("Portal Customer", "Customer"), ("trading", "services", "tourism", "car_rental", "education", "restaurant", "property", "agriculture", "engineering", "construction", "manufacturing")),
	SubPortalDef("doctor", "enable_doctor_portal", "👨‍⚕️", "بوابة الأطباء", "Doctors", "/portal/doctor", ("Portal Doctor",), ("healthcare",)),
	SubPortalDef("supplier", "enable_supplier_portal", "📦", "بوابة الموردين", "Suppliers", "/portal/supplier", ("Portal Supplier",), ("trading", "manufacturing", "agriculture", "construction")),
	SubPortalDef("loan", "enable_loan_portal", "💳", "بوابة عملاء التمويل", "Loan Clients", "/portal/loan", ("Portal Loan Client", "Customer"), ("finance", "leasing")),
)


def installed_apps() -> set[str]:
	return set(frappe.get_installed_apps() or [])


def get_company_business_activity(company: str) -> str:
	if not company or not frappe.db.exists("Company", company):
		return "General"
	row = frappe.db.get_value(
		"Company",
		company,
		["business_activity", "industry_sector", "production_demo_activity"],
		as_dict=True,
	) or {}
	for key in ("business_activity", "industry_sector", "production_demo_activity"):
		val = (row.get(key) or "").strip()
		if val and val.lower() not in ("", "general"):
			return _normalize_company_activity(val)
	return "General"


def primary_vertical_id_for_activity(activity: str) -> str:
	return COMPANY_ACTIVITY_PRIMARY_VERTICAL.get(activity, "")


def activity_profile(activity: str) -> dict:
	base = ACTIVITY_PROFILES.get("General", {})
	specific = ACTIVITY_PROFILES.get(activity, {})
	return {**base, **specific}


def vertical_by_id(vertical_id: str) -> VerticalDef | None:
	for row in VERTICALS:
		if row.id == vertical_id:
			return row
	return None


def sub_portal_by_id(sub_portal_id: str) -> SubPortalDef | None:
	for row in SUB_PORTALS:
		if row.id == sub_portal_id:
			return row
	return None


def _vertical_allowed_for_company(row: VerticalDef, activity: str, primary_id: str) -> bool:
	if activity == "General":
		return row.id == "services" or (primary_id and row.id == primary_id)
	if primary_id:
		if row.id == primary_id:
			return True
		# Tourism companies may also expose car rental when app is installed
		if activity in ("Tourism", "Hotel Assets") and row.id == "car_rental":
			return True
		if activity == "Financial Services" and row.id == "leasing":
			return True
		return False
	return activity in row.company_activities


def _hub_allows(hub, field: str) -> bool:
	if cint(getattr(hub, "follow_company_activity", 1)):
		return True
	return cint(getattr(hub, field, 1))


def list_active_verticals(hub) -> list[dict]:
	activity = get_company_business_activity(hub.company)
	primary_id = primary_vertical_id_for_activity(activity)
	follow = cint(getattr(hub, "follow_company_activity", 1))
	apps = installed_apps()
	out: list[dict] = []

	for row in VERTICALS:
		if row.app not in apps:
			continue
		if follow:
			if not _vertical_allowed_for_company(row, activity, primary_id):
				continue
		elif not cint(getattr(hub, row.hub_field, 0)):
			continue
		out.append(
			{
				"id": row.id,
				"icon": row.icon,
				"name_ar": row.name_ar,
				"name_en": row.name_en,
				"route": row.route,
				"sub_portals": list(row.sub_portals),
				"app": row.app,
				"is_primary": row.id == primary_id or (not primary_id and len(out) == 0),
			}
		)

	# Single primary vertical only for dedicated activities
	if primary_id and out:
		primary_rows = [v for v in out if v["id"] == primary_id]
		if primary_rows:
			extra = [v for v in out if v["id"] != primary_id and v["id"] in ("car_rental", "leasing")]
			out = primary_rows[:1] + extra

	return out


def list_active_sub_portals(hub, verticals: list[dict] | None = None) -> list[dict]:
	verticals = verticals or list_active_verticals(hub)
	follow = cint(getattr(hub, "follow_company_activity", 1))
	active_vertical_ids = {v["id"] for v in verticals}
	out: list[dict] = []
	for row in SUB_PORTALS:
		if follow:
			if not active_vertical_ids.intersection(row.verticals):
				continue
		elif not cint(getattr(hub, row.hub_field, 0)):
			continue
		else:
			if not active_vertical_ids.intersection(row.verticals):
				continue
		out.append(
			{
				"id": row.id,
				"icon": row.icon,
				"name_ar": row.name_ar,
				"name_en": row.name_en,
				"route": row.route,
				"roles": list(row.roles),
			}
		)
	return out


def cint(value) -> int:
	from frappe.utils import cint as _cint

	return _cint(value)
