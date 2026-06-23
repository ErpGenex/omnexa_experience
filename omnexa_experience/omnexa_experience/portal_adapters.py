# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Adapters that delegate portal data to installed vertical apps."""

from __future__ import annotations

import frappe
from frappe.utils import flt, getdate, today


def _has_app(app_name: str) -> bool:
	return app_name in (frappe.get_installed_apps() or [])


def get_vertical_snapshot(*, vertical_id: str, company: str, branch: str | None = None) -> dict:
	branch = branch or frappe.db.get_value("Branch", {"company": company}, "name")
	base = {"vertical": vertical_id, "company": company, "branch": branch, "items": [], "actions": []}

	if vertical_id == "healthcare" and _has_app("omnexa_healthcare"):
		return _healthcare_snapshot(company, branch, base)
	if vertical_id == "trading" and _has_app("omnexa_trading"):
		return _commerce_snapshot(company, branch, base, label="Trading catalog")
	if vertical_id == "manufacturing" and _has_app("omnexa_manufacturing"):
		return _commerce_snapshot(company, branch, base, label="Manufacturing services")
	if vertical_id == "services" and _has_app("omnexa_services"):
		return _commerce_snapshot(company, branch, base, label="Service catalog")
	if vertical_id == "car_rental" and _has_app("omnexa_car_rental"):
		return _booking_snapshot(company, branch, base, label="Available vehicles")
	if vertical_id == "education" and _has_app("omnexa_education"):
		return _education_snapshot(company, branch, base)
	if vertical_id in ("finance",) and _has_app("omnexa_consumer_finance"):
		return _finance_snapshot(company, branch, base, vertical_id)
	if vertical_id == "leasing" and _has_app("omnexa_leasing_finance"):
		return _finance_snapshot(company, branch, base, vertical_id)
	if vertical_id == "tourism" and _has_app("omnexa_tourism"):
		return _tourism_snapshot(company, branch, base)
	if vertical_id == "restaurant" and _has_app("omnexa_restaurant"):
		return _commerce_snapshot(company, branch, base, label="Menu & orders")
	if vertical_id == "property" and _has_app("erpgenex_property_mgmt"):
		return _property_snapshot(company, branch, base)
	if vertical_id == "agriculture" and _has_app("omnexa_agriculture"):
		return _commerce_snapshot(company, branch, base, label="Agri products")
	if vertical_id == "engineering" and _has_app("omnexa_engineering_consulting"):
		return _engineering_snapshot(company, branch, base)
	if vertical_id == "construction" and _has_app("omnexa_construction"):
		return _construction_snapshot(company, branch, base)

	return base


def get_sub_portal_dashboard(*, sub_portal: str, company: str, branch: str | None = None, user: str | None = None) -> dict:
	user = user or frappe.session.user
	branch = branch or frappe.db.get_value("Branch", {"company": company}, "name")
	email = frappe.db.get_value("User", user, "email") if user and user != "Guest" else None
	base = {"sub_portal": sub_portal, "company": company, "branch": branch, "user": user, "cards": [], "lists": []}

	if sub_portal == "patient":
		return _patient_dashboard(company, branch, user, email, base)
	if sub_portal == "customer":
		return _customer_dashboard(company, branch, email, base)
	if sub_portal == "doctor":
		return _doctor_dashboard(company, branch, user, email, base)
	if sub_portal == "supplier":
		return _supplier_dashboard(company, branch, user, email, base)
	if sub_portal == "loan":
		return _loan_dashboard(company, branch, user, email, base)

	return base


def _healthcare_snapshot(company: str, branch: str | None, base: dict) -> dict:
	out = dict(base)
	if branch and frappe.db.exists("DocType", "Healthcare Branch Website"):
		slug = frappe.db.get_value("Healthcare Branch Website", {"branch": branch, "is_enabled": 1}, "site_slug")
		if slug:
			out["actions"].append({"label": "Hospital website", "url": f"/hospital?site={slug}"})
			out["actions"].append({"label": "Book appointment", "url": f"/hospital/booking?site={slug}"})
	if branch and frappe.db.exists("DocType", "Healthcare Service Catalog"):
		services = frappe.get_all(
			"Healthcare Service Catalog",
			filters={"company": company, "branch": branch, "is_active": 1, "publish_on_website": 1},
			fields=["service_title", "default_rate", "service_code"],
			limit=6,
		)
		out["items"] = services
	return out


def _commerce_snapshot(company: str, branch: str | None, base: dict, label: str) -> dict:
	out = dict(base)
	out["label"] = label
	if frappe.db.exists("DocType", "Catalog Item"):
		items = frappe.get_all(
			"Catalog Item",
			filters={"company": company, "published": 1},
			fields=["title_en", "title_ar", "slug", "item_type"],
			limit=8,
		)
		out["items"] = items
		out["actions"].append({"label": "Browse shop", "url": f"/portal/customer?company={company}"})
	return out


def _booking_snapshot(company: str, branch: str | None, base: dict, label: str) -> dict:
	out = dict(base)
	out["label"] = label
	if frappe.db.exists("DocType", "Bookable Resource"):
		resources = frappe.get_all(
			"Bookable Resource",
			filters={"company": company, "is_active": 1},
			fields=["resource_name", "resource_type"],
			limit=8,
		)
		out["items"] = resources
	return out


def _education_snapshot(company: str, branch: str | None, base: dict) -> dict:
	out = dict(base)
	if frappe.db.exists("DocType", "Education Institution"):
		institutions = frappe.get_all(
			"Education Institution",
			filters={"company": company},
			fields=["name", "institution_name"],
			limit=5,
		)
		out["items"] = institutions
		out["actions"].extend(
			[
				{"label": "Apply online", "url": "/education/apply"},
				{"label": "Student portal", "url": "/app/education-student-portal"},
				{"label": "Parent portal", "url": "/app/education-parent-mobile"},
			]
		)
	return out


def _finance_snapshot(company: str, branch: str | None, base: dict, vertical_id: str) -> dict:
	out = dict(base)
	out["label"] = "Loan products" if vertical_id == "finance" else "Leasing products"
	if frappe.db.exists("DocType", "Loan Product"):
		products = frappe.get_all(
			"Loan Product",
			filters={"company": company, "disabled": 0},
			fields=["name", "product_name"],
			limit=6,
		)
		out["items"] = products
	out["actions"].append({"label": "Loan client portal", "url": f"/portal/loan?company={company}"})
	return out


def _tourism_snapshot(company: str, branch: str | None, base: dict) -> dict:
	out = dict(base)
	out["actions"].append({"label": "Tourism booking", "url": f"/tourism?company={company}&branch={branch or ''}"})
	if frappe.db.exists("DocType", "Tourism Property"):
		props = frappe.get_all(
			"Tourism Property",
			filters={"company": company},
			fields=["property_name"],
			limit=6,
		)
		out["items"] = props
	return out


def _property_snapshot(company: str, branch: str | None, base: dict) -> dict:
	out = dict(base)
	if frappe.db.exists("DocType", "Lease Contract"):
		leases = frappe.db.count("Lease Contract", {"company": company, "status": "Active"})
		out["items"] = [{"label": "Active leases", "count": leases}]
	return out


def _engineering_snapshot(company: str, branch: str | None, base: dict) -> dict:
	out = dict(base)
	out["actions"].append({"label": "Client submittals", "url": "/engineering-consulting-submittals"})
	return out


def _construction_snapshot(company: str, branch: str | None, base: dict) -> dict:
	out = dict(base)
	out["label"] = "Construction projects"
	if frappe.db.exists("DocType", "Construction Project"):
		projects = frappe.get_all(
			"Construction Project",
			filters={"company": company},
			fields=["name", "project_name", "status"],
			limit=6,
			order_by="modified desc",
		)
		out["items"] = projects
	return out


def _patient_dashboard(company, branch, user, email, base):
	out = dict(base)
	if user == "Guest":
		out["cards"].append({"title": "Register", "text": "Create a patient account", "action": "register"})
		return out
	patient = None
	if email and frappe.db.exists("DocType", "Healthcare Patient Telecom"):
		row = frappe.db.sql(
			"""SELECT parent FROM `tabHealthcare Patient Telecom`
			WHERE value=%s AND parenttype='Healthcare Patient' LIMIT 1""",
			email,
		)
		if row:
			patient = row[0][0]
	if patient and _has_app("omnexa_healthcare"):
		try:
			from omnexa_healthcare.api.portal import get_my_appointments

			out["lists"].append({"title": "Appointments", "rows": get_my_appointments(patient)})
		except Exception:
			pass
	out["cards"].append({"title": "Book appointment", "url": f"/hospital/booking?company={company}&branch={branch or ''}"})
	return out


def _customer_dashboard(company, branch, email, base):
	out = dict(base)
	if frappe.db.exists("DocType", "Web Order") and email:
		orders = frappe.get_all(
			"Web Order",
			filters={"company": company, "customer_email": email},
			fields=["name", "status", "grand_total", "modified"],
			limit=10,
			order_by="modified desc",
		)
		out["lists"].append({"title": "My orders", "rows": orders})
	if frappe.db.exists("DocType", "Booking") and email:
		bookings = frappe.get_all(
			"Booking",
			filters={"company": company, "customer_email": email},
			fields=["name", "status", "start_datetime", "end_datetime"],
			limit=10,
			order_by="modified desc",
		)
		out["lists"].append({"title": "My bookings", "rows": bookings})
	out["cards"].append({"title": "Shop", "url": f"/portal?company={company}"})
	return out


def _doctor_dashboard(company, branch, user, email, base):
	out = dict(base)
	practitioner = None
	if email and frappe.db.exists("DocType", "Healthcare Practitioner"):
		practitioner = frappe.db.get_value("Healthcare Practitioner", {"user": user, "company": company}, "name")
	if practitioner:
		appts = frappe.get_all(
			"Healthcare Appointment",
			filters={"practitioner": practitioner, "appointment_date": [">=", today()]},
			fields=["name", "patient", "appointment_date", "status"],
			limit=20,
			order_by="appointment_date asc",
		)
		out["lists"].append({"title": "Upcoming appointments", "rows": appts})
	else:
		out["cards"].append({"title": "Link practitioner profile", "text": "Contact admin to link your user account."})
	return out


def _supplier_dashboard(company, branch, user, email, base):
	out = dict(base)
	if frappe.db.exists("DocType", "Purchase Order"):
		pos = frappe.get_all(
			"Purchase Order",
			filters={"company": company, "docstatus": 1},
			fields=["name", "supplier", "grand_total", "transaction_date", "status"],
			limit=10,
			order_by="modified desc",
		)
		out["lists"].append({"title": "Recent purchase orders", "rows": pos})
	out["cards"].append({"title": "Submit delivery note", "text": "Contact procurement to enable supplier ASN workflow."})
	return out


def _loan_dashboard(company, branch, user, email, base):
	out = dict(base)
	for dt, title in (("Loan Application", "Loan applications"), ("Loan Contract", "Active loans")):
		if frappe.db.exists("DocType", dt):
			filters = {"company": company}
			if email and frappe.db.has_column(dt, "applicant_email"):
				filters["applicant_email"] = email
			rows = frappe.get_all(dt, filters=filters, fields=["name", "status"], limit=10, order_by="modified desc")
			if rows:
				out["lists"].append({"title": title, "rows": rows})
	out["cards"].append({"title": "Apply for financing", "text": "Submit a new loan application through your branch."})
	return out
