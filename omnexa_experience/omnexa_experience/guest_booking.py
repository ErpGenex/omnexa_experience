# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""
Guest booking: list resources, list confirmed blocks, **hold → confirm**, create/cancel.

HTTP: methods under ``omnexa_experience.omnexa_experience.guest_booking``.

Optional ``idempotency_key`` on create is stored in **Default** (``frappe.db.set_default``) so retries return the same booking.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import add_to_date, cint, get_datetime, now_datetime


def _idem_default_key(company: str, key: str) -> str:
	"""Site-defaults key for booking idempotency (DB-backed, reliable in tests and prod)."""
	return f"omnx_guest_booking_idem:{company}:{key}"


def _serialize_booking_dict(d: dict) -> dict:
	return {
		"name": d["name"],
		"company": d["company"],
		"bookable_resource": d["bookable_resource"],
		"start_datetime": d["start_datetime"],
		"end_datetime": d["end_datetime"],
		"customer_email": d.get("customer_email") or "",
		"payment_intent": d.get("payment_intent") or None,
		"status": d["status"],
		"hold_expires_at": d.get("hold_expires_at"),
	}


def _serialize_booking_doc(b) -> dict:
	return _serialize_booking_dict(
		{
			"name": b.name,
			"company": b.company,
			"bookable_resource": b.bookable_resource,
			"start_datetime": b.start_datetime,
			"end_datetime": b.end_datetime,
			"customer_email": b.customer_email,
			"payment_intent": b.payment_intent,
			"status": b.status,
			"hold_expires_at": getattr(b, "hold_expires_at", None),
		}
	)


def _fetch_booking_dict(name: str, company: str) -> dict | None:
	rows = frappe.get_all(
		"Booking",
		filters={"name": name, "company": company},
		fields=[
			"name",
			"company",
			"bookable_resource",
			"start_datetime",
			"end_datetime",
			"customer_email",
			"payment_intent",
			"status",
			"hold_expires_at",
		],
		ignore_permissions=True,
		limit=1,
	)
	return rows[0] if rows else None


@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(limit=60, seconds=60, methods=["GET"])
def list_bookable_resources(company: str | None = None):
	"""List ``Bookable Resource`` rows for a company."""
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("A valid company is required."), title=_("Booking"))
	rows = frappe.get_all(
		"Bookable Resource",
		filters={"company": company},
		fields=[
			"name",
			"resource_name",
			"slot_duration_minutes",
			"buffer_minutes",
			"timezone",
		],
		order_by="resource_name asc",
		ignore_permissions=True,
	)
	return {"resources": rows}


@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(limit=60, seconds=60, methods=["GET"])
def list_confirmed_bookings_for_resource(
	company: str | None = None,
	bookable_resource: str | None = None,
	start: str | None = None,
	end: str | None = None,
):
	"""Return **Confirmed** bookings for one resource whose interval intersects ``[start, end]``."""
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("A valid company is required."), title=_("Booking"))
	if not bookable_resource or not frappe.db.exists("Bookable Resource", bookable_resource):
		frappe.throw(_("bookable_resource is required."), title=_("Booking"))
	res_co = frappe.db.get_value("Bookable Resource", bookable_resource, "company")
	if res_co != company:
		frappe.throw(_("Resource does not belong to this company."), title=_("Booking"))
	if not start or not end:
		frappe.throw(_("start and end datetimes are required."), title=_("Booking"))
	s1 = get_datetime(start)
	e1 = get_datetime(end)
	if s1 >= e1:
		frappe.throw(_("end must be after start."), title=_("Booking"))

	rows = frappe.get_all(
		"Booking",
		filters={
			"company": company,
			"bookable_resource": bookable_resource,
			"status": "Confirmed",
			"start_datetime": ["<", end],
			"end_datetime": [">", start],
		},
		fields=["name", "start_datetime", "end_datetime", "customer_email"],
		order_by="start_datetime asc",
		ignore_permissions=True,
	)
	return {"bookings": rows}


def _create_guest_booking_impl(
	company: str | None = None,
	bookable_resource: str | None = None,
	start_datetime: str | None = None,
	end_datetime: str | None = None,
	customer_email: str | None = None,
	payment_intent: str | None = None,
	status: str | None = None,
	idempotency_key: str | None = None,
	hold_ttl_minutes: int | str | None = None,
):
	"""Internal create (no HTTP rate-limit decorator — used by multiple whitelisted entrypoints)."""
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("A valid company is required."), title=_("Booking"))

	key = (idempotency_key or "").strip()
	if key:
		prev = frappe.db.get_default(_idem_default_key(company, key))
		if prev and frappe.db.exists("Booking", prev):
			row = _fetch_booking_dict(prev, company)
			if row:
				return _serialize_booking_dict(row)

	if not bookable_resource or not frappe.db.exists("Bookable Resource", bookable_resource):
		frappe.throw(_("bookable_resource is required."), title=_("Booking"))
	res_co = frappe.db.get_value("Bookable Resource", bookable_resource, "company")
	if res_co != company:
		frappe.throw(_("Resource does not belong to this company."), title=_("Booking"))

	st = (status or "Confirmed").strip()
	if st not in ("Draft", "Confirmed"):
		frappe.throw(_("status must be Draft or Confirmed."), title=_("Booking"))

	b = frappe.new_doc("Booking")
	b.company = company
	b.bookable_resource = bookable_resource
	b.start_datetime = start_datetime
	b.end_datetime = end_datetime
	b.customer_email = (customer_email or "").strip()
	if payment_intent and frappe.db.exists("Payment Intent", payment_intent):
		b.payment_intent = payment_intent
	b.status = st
	if st == "Draft":
		ttl = cint(hold_ttl_minutes) if hold_ttl_minutes is not None else 15
		if ttl < 1 or ttl > 120:
			frappe.throw(_("hold_ttl_minutes must be between 1 and 120."), title=_("Booking"))
		b.hold_expires_at = add_to_date(now_datetime(), minutes=ttl)
	else:
		b.hold_expires_at = None
	b.flags.ignore_permissions = True
	b.insert(ignore_permissions=True)

	if key:
		frappe.db.set_default(_idem_default_key(company, key), b.name)

	return _serialize_booking_doc(b)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=3600, methods=["POST"])
def create_guest_booking(
	company: str | None = None,
	bookable_resource: str | None = None,
	start_datetime: str | None = None,
	end_datetime: str | None = None,
	customer_email: str | None = None,
	payment_intent: str | None = None,
	status: str | None = None,
	idempotency_key: str | None = None,
	hold_ttl_minutes: int | str | None = None,
):
	"""
	Create a **Confirmed** or **Draft** booking (draft = timed hold).

	For ``status=Draft``, set ``hold_ttl_minutes`` (default **15**, max **120**); ``hold_expires_at`` is stored.
	Optional ``idempotency_key``: same key + company returns the existing booking.
	"""
	return _create_guest_booking_impl(
		company=company,
		bookable_resource=bookable_resource,
		start_datetime=start_datetime,
		end_datetime=end_datetime,
		customer_email=customer_email,
		payment_intent=payment_intent,
		status=status,
		idempotency_key=idempotency_key,
		hold_ttl_minutes=hold_ttl_minutes,
	)


@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(limit=60, seconds=60, methods=["GET"])
def get_guest_booking(booking: str | None = None, company: str | None = None):
	if not booking:
		frappe.throw(_("Booking not found."), frappe.DoesNotExistError, title=_("Booking"))
	if not company:
		frappe.throw(_("A valid company is required."), title=_("Booking"))
	row = _fetch_booking_dict(booking, company)
	if not row:
		frappe.throw(_("Booking not found."), frappe.DoesNotExistError, title=_("Booking"))
	return _serialize_booking_dict(row)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=30, seconds=3600, methods=["POST"])
def cancel_guest_booking(booking: str | None = None, company: str | None = None):
	"""Set booking status to **Cancelled** (idempotent)."""
	if not booking:
		frappe.throw(_("Booking not found."), frappe.DoesNotExistError, title=_("Booking"))
	if not company:
		frappe.throw(_("A valid company is required."), title=_("Booking"))
	row = _fetch_booking_dict(booking, company)
	if not row:
		frappe.throw(_("Booking not found."), frappe.DoesNotExistError, title=_("Booking"))
	if row["status"] == "Cancelled":
		return _serialize_booking_dict(row)
	frappe.db.set_value("Booking", booking, "status", "Cancelled", update_modified=True)
	out = _fetch_booking_dict(booking, company)
	return _serialize_booking_dict(out) if out else _serialize_booking_dict(row)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=25, seconds=3600, methods=["POST"])
def create_guest_booking_hold(
	company: str | None = None,
	bookable_resource: str | None = None,
	start_datetime: str | None = None,
	end_datetime: str | None = None,
	customer_email: str | None = None,
	payment_intent: str | None = None,
	idempotency_key: str | None = None,
	hold_ttl_minutes: int | str | None = 15,
):
	"""Create a **Draft** booking with ``hold_ttl_minutes`` (default 15). Same args as ``create_guest_booking`` except status is forced to Draft."""
	return _create_guest_booking_impl(
		company=company,
		bookable_resource=bookable_resource,
		start_datetime=start_datetime,
		end_datetime=end_datetime,
		customer_email=customer_email,
		payment_intent=payment_intent,
		status="Draft",
		idempotency_key=idempotency_key,
		hold_ttl_minutes=hold_ttl_minutes,
	)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=25, seconds=3600, methods=["POST"])
def confirm_guest_booking(
	booking: str | None = None,
	company: str | None = None,
	payment_intent: str | None = None,
):
	"""
	Promote a **Draft** hold to **Confirmed**. Idempotent if already confirmed.
	Raises if the hold TTL has passed (``hold_expires_at`` < now).
	"""
	if not booking or not frappe.db.exists("Booking", booking):
		frappe.throw(_("Booking not found."), frappe.DoesNotExistError, title=_("Booking"))
	if not company:
		frappe.throw(_("A valid company is required."), title=_("Booking"))
	row = _fetch_booking_dict(booking, company)
	if not row:
		frappe.throw(_("Booking not found."), frappe.DoesNotExistError, title=_("Booking"))
	if row["status"] == "Confirmed":
		return _serialize_booking_dict(row)
	if row["status"] != "Draft":
		frappe.throw(_("Only draft holds can be confirmed."), title=_("Booking"))
	exp = row.get("hold_expires_at")
	if exp and get_datetime(exp) < now_datetime():
		frappe.throw(_("Hold expired. Create a new hold."), title=_("Booking"))

	prev_user = frappe.session.user
	frappe.set_user("Administrator")
	try:
		doc = frappe.get_doc("Booking", booking)
		if doc.company != company:
			frappe.throw(_("Booking does not belong to this company."), title=_("Booking"))
		if payment_intent:
			doc.payment_intent = payment_intent
		doc.status = "Confirmed"
		doc.hold_expires_at = None
		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)
	finally:
		frappe.set_user(prev_user)

	out = _fetch_booking_dict(booking, company)
	return _serialize_booking_dict(out) if out else _serialize_booking_dict(row)
