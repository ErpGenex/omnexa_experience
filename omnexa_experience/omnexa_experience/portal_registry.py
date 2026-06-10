# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Registry of business verticals and sub-portals for the unified Omnexa portal."""

from __future__ import annotations

from dataclasses import dataclass

import frappe


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


VERTICALS: tuple[VerticalDef, ...] = (
	VerticalDef("healthcare", "omnexa_healthcare", "enable_healthcare", "🏥", "الصحة والعيادات", "Healthcare", "/portal/vertical/healthcare", ("patient", "doctor")),
	VerticalDef("trading", "omnexa_trading", "enable_trading", "🛒", "التجارة", "Trading & Commerce", "/portal/vertical/trading", ("customer", "supplier")),
	VerticalDef("manufacturing", "omnexa_manufacturing", "enable_manufacturing", "🏭", "التصنيع", "Manufacturing", "/portal/vertical/manufacturing", ("customer", "supplier")),
	VerticalDef("services", "omnexa_services", "enable_services", "🔧", "الخدمات", "Professional Services", "/portal/vertical/services", ("customer",)),
	VerticalDef("car_rental", "omnexa_car_rental", "enable_car_rental", "🚗", "تأجير السيارات", "Car Rental", "/portal/vertical/car-rental", ("customer",)),
	VerticalDef("education", "omnexa_education", "enable_education", "🎓", "التعليم", "Education", "/portal/vertical/education", ("customer",)),
	VerticalDef("finance", "omnexa_consumer_finance", "enable_finance", "🏦", "التمويل والبنوك", "Finance & Banking", "/portal/vertical/finance", ("loan", "customer")),
	VerticalDef("leasing", "omnexa_leasing_finance", "enable_leasing", "📋", "الإيجار التمويلي", "Leasing", "/portal/vertical/leasing", ("loan", "customer")),
	VerticalDef("tourism", "omnexa_tourism", "enable_tourism", "🏨", "السياحة والضيافة", "Tourism", "/portal/vertical/tourism", ("customer",)),
	VerticalDef("restaurant", "omnexa_restaurant", "enable_restaurant", "🍽️", "المطاعم", "Restaurant", "/portal/vertical/restaurant", ("customer",)),
	VerticalDef("property", "erpgenex_property_mgmt", "enable_property", "🏢", "العقارات", "Property", "/portal/vertical/property", ("customer",)),
	VerticalDef("agriculture", "omnexa_agriculture", "enable_agriculture", "🌾", "الزراعة", "Agriculture", "/portal/vertical/agriculture", ("customer", "supplier")),
	VerticalDef("engineering", "omnexa_engineering_consulting", "enable_engineering", "📐", "الاستشارات الهندسية", "Engineering", "/portal/vertical/engineering", ("customer",)),
)

SUB_PORTALS: tuple[SubPortalDef, ...] = (
	SubPortalDef("patient", "enable_patient_portal", "🩺", "بوابة المرضى", "Patients", "/portal/patient", ("Patient Portal User", "Customer"), ("healthcare",)),
	SubPortalDef("customer", "enable_customer_portal", "👤", "بوابة العملاء", "Customers", "/portal/customer", ("Portal Customer", "Customer"), ("trading", "services", "tourism", "car_rental", "education", "restaurant", "property", "agriculture", "engineering")),
	SubPortalDef("doctor", "enable_doctor_portal", "👨‍⚕️", "بوابة الأطباء", "Doctors", "/portal/doctor", ("Portal Doctor",), ("healthcare",)),
	SubPortalDef("supplier", "enable_supplier_portal", "📦", "بوابة الموردين", "Suppliers", "/portal/supplier", ("Portal Supplier",), ("trading", "manufacturing", "agriculture")),
	SubPortalDef("loan", "enable_loan_portal", "💳", "بوابة عملاء التمويل", "Loan Clients", "/portal/loan", ("Portal Loan Client", "Customer"), ("finance", "leasing")),
)


def installed_apps() -> set[str]:
	return set(frappe.get_installed_apps() or [])


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


def list_active_verticals(hub) -> list[dict]:
	apps = installed_apps()
	out: list[dict] = []
	for row in VERTICALS:
		if row.app not in apps:
			continue
		if not cint(getattr(hub, row.hub_field, 1)):
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
			}
		)
	return out


def list_active_sub_portals(hub, verticals: list[dict] | None = None) -> list[dict]:
	active_vertical_ids = {v["id"] for v in (verticals or list_active_verticals(hub))}
	out: list[dict] = []
	for row in SUB_PORTALS:
		if not cint(getattr(hub, row.hub_field, 1)):
			continue
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
