# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import hashlib
import hmac
import json
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime

from omnexa_core.omnexa_core.test_data import create_test_company, ensure_pilot_geo
from omnexa_experience.omnexa_experience.guest_catalog import (
	create_guest_cart_web_order,
	get_published_catalog_item,
	list_published_catalog_items,
)
from omnexa_experience.omnexa_experience.guest_booking import (
	cancel_guest_booking,
	confirm_guest_booking,
	create_guest_booking,
	create_guest_booking_hold,
	get_guest_booking,
	list_bookable_resources,
	list_confirmed_bookings_for_resource,
)
from omnexa_experience.omnexa_experience.guest_checkout import (
	get_guest_web_order,
	submit_guest_web_order,
)
from omnexa_experience.omnexa_experience.payment_webhook import process_payment_intent_webhook
from omnexa_experience.omnexa_experience.portal_me import (
	get_my_booking,
	get_my_web_order,
	list_my_bookings,
	list_my_web_orders,
)
from omnexa_experience.omnexa_experience.web_theme import (
	HEAD_MARKER,
	preview_theme_head,
	update_website_context,
)
from omnexa_experience.omnexa_experience.theme_preview import (
	before_request_theme_preview,
	create_theme_preview_token,
)
from omnexa_theme_manager.desk_theme import get_desk_theme_payload
from omnexa_experience.omnexa_experience.doctype.experience_tenant_theme.experience_tenant_theme import (
	compare_themes,
	list_theme_publish_history,
	publish_theme,
	rollback_theme,
	rollback_theme_to,
)


class TestOmnexaExperience(FrappeTestCase):
	def setUp(self):
		super().setUp()
		ensure_pilot_geo()
		self.company = create_test_company("OMNX-EXP")
		self.branch = self._ensure_branch()

	def _ensure_branch(self):
		existing = frappe.db.get_value(
			"Branch", {"company": self.company, "status": "Active"}, "name", order_by="creation asc"
		)
		if existing:
			return existing
		doc = frappe.new_doc("Branch")
		doc.company = self.company
		doc.branch_name = "Experience Test Branch"
		doc.branch_code = f"EXP{frappe.generate_hash(length=4).upper()[:4]}"
		doc.status = "Active"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _catalog(self, slug="sku-1"):
		slug = f"{slug}-{frappe.generate_hash(length=6)}"
		c = frappe.new_doc("Catalog Item")
		c.company = self.company
		c.slug = slug
		c.title_en = "Item"
		c.title_ar = "صنف"
		c.item_type = "product"
		c.published = 1
		c.insert(ignore_permissions=True)
		return c.name

	def _income_gl(self, number="8800", name="Web Checkout Revenue"):
		if frappe.db.exists("GL Account", {"company": self.company, "account_number": number}):
			return frappe.db.get_value(
				"GL Account", {"company": self.company, "account_number": number}, "name"
			)
		g = frappe.new_doc("GL Account")
		g.company = self.company
		g.account_number = number
		g.account_name = name
		g.is_group = 0
		g.account_type = "Income"
		g.insert(ignore_permissions=True)
		return g.name

	def test_web_order_idempotency_key_unique(self):
		ci = self._catalog("sku-idem")
		wo1 = frappe.new_doc("Web Order")
		wo1.company = self.company
		wo1.idempotency_key = "idem-1"
		wo1.append("lines", {"catalog_item": ci, "qty": 1, "rate": 10})
		wo1.insert(ignore_permissions=True)
		wo2 = frappe.new_doc("Web Order")
		wo2.company = self.company
		wo2.idempotency_key = "idem-1"
		wo2.append("lines", {"catalog_item": ci, "qty": 1, "rate": 5})
		with self.assertRaises(frappe.ValidationError):
			wo2.insert(ignore_permissions=True)

	def test_booking_overlap_rejected(self):
		res = frappe.new_doc("Bookable Resource")
		res.company = self.company
		res.resource_name = "Room A"
		res.slot_duration_minutes = 60
		res.insert(ignore_permissions=True)
		start = now_datetime()
		end = add_to_date(start, hours=1)
		intent = self._create_payment_intent()
		b1 = frappe.new_doc("Booking")
		b1.company = self.company
		b1.bookable_resource = res.name
		b1.start_datetime = start
		b1.end_datetime = end
		b1.customer_email = "overlap@example.com"
		b1.payment_intent = intent.name
		b1.status = "Confirmed"
		b1.insert(ignore_permissions=True)
		b2 = frappe.new_doc("Booking")
		b2.company = self.company
		b2.bookable_resource = res.name
		b2.start_datetime = add_to_date(start, minutes=30)
		b2.end_datetime = add_to_date(end, minutes=30)
		b2.customer_email = "other@example.com"
		b2.payment_intent = intent.name
		b2.status = "Confirmed"
		with self.assertRaises(frappe.ValidationError):
			b2.insert(ignore_permissions=True)

	def _create_payment_intent(self):
		intent = frappe.new_doc("Payment Intent")
		intent.company = self.company
		intent.amount = 100
		intent.currency = "EGP"
		intent.insert(ignore_permissions=True)
		return intent

	def test_payment_webhook_updates_payment_intent_status(self):
		intent = self._create_payment_intent()
		payload = {
			"payment_intent": intent.name,
			"status": "succeeded",
			"provider_reference": "txn-001",
		}
		raw = json.dumps(payload, sort_keys=True)
		secret = "test-secret"
		signature = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
		result = process_payment_intent_webhook(
			event_id="evt-pay-1",
			payload=payload,
			received_signature=signature,
			secret=secret,
		)
		self.assertEqual(result["status"], "processed")
		intent.reload()
		self.assertEqual(intent.status, "succeeded")
		self.assertEqual(intent.client_secret_ref, "txn-001")

	def test_payment_webhook_duplicate_event_is_idempotent(self):
		intent = self._create_payment_intent()
		payload = {
			"payment_intent": intent.name,
			"status": "processing",
			"provider_reference": "txn-dup-001",
		}
		process_payment_intent_webhook(event_id="evt-pay-dup", payload=payload)
		result = process_payment_intent_webhook(event_id="evt-pay-dup", payload=payload)
		self.assertEqual(result["status"], "duplicate")

	def test_guest_catalog_lists_published_only(self):
		pub = self._catalog("guest-api-pub")
		pub_slug = frappe.db.get_value("Catalog Item", pub, "slug")
		frappe.db.set_value("Catalog Item", pub, "published", 1, update_modified=False)
		priv = self._catalog("guest-api-priv")
		priv_slug = frappe.db.get_value("Catalog Item", priv, "slug")
		frappe.db.set_value("Catalog Item", priv, "published", 0, update_modified=False)
		frappe.set_user("Guest")
		try:
			out = list_published_catalog_items(company=self.company)
		finally:
			frappe.set_user("Administrator")
		slugs = {r["slug"] for r in out["items"]}
		self.assertIn(pub_slug, slugs)
		self.assertNotIn(priv_slug, slugs)

	def test_guest_catalog_get_by_slug(self):
		ci = self._catalog("slug-detail-1")
		slug = frappe.db.get_value("Catalog Item", ci, "slug")
		frappe.db.set_value("Catalog Item", ci, "published", 1, update_modified=False)
		frappe.set_user("Guest")
		try:
			row = get_published_catalog_item(company=self.company, slug=slug)
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(row["slug"], slug)
		self.assertEqual(row["name"], ci)

	def test_guest_cart_creates_draft_web_order(self):
		ci = self._catalog("cart-line-a")
		frappe.db.set_value("Catalog Item", ci, "published", 1, update_modified=False)
		lines = [{"catalog_item": ci, "qty": 2, "rate": 15.5}]
		frappe.set_user("Guest")
		try:
			out1 = create_guest_cart_web_order(
				company=self.company,
				idempotency_key="cart-key-1",
				lines=lines,
			)
			out2 = create_guest_cart_web_order(
				company=self.company,
				idempotency_key="cart-key-1",
				lines=lines,
			)
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(out1["name"], out2["name"])
		self.assertEqual(out1["status"], "Draft")
		self.assertEqual(out1["grand_total"], 31.0)
		wo = frappe.get_doc("Web Order", out1["name"])
		self.assertEqual(wo.docstatus, 0)

	def test_guest_cart_stores_customer_email(self):
		ci = self._catalog("cart-email-1")
		frappe.db.set_value("Catalog Item", ci, "published", 1, update_modified=False)
		lines = [{"catalog_item": ci, "qty": 1, "rate": 10}]
		frappe.set_user("Guest")
		try:
			out = create_guest_cart_web_order(
				company=self.company,
				idempotency_key="cart-email-key-1",
				lines=lines,
				customer_email="Buyer@Example.com",
			)
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(out.get("customer_email"), "buyer@example.com")
		wo = frappe.get_doc("Web Order", out["name"])
		self.assertEqual((wo.customer_email or "").lower(), "buyer@example.com")

	def test_guest_cart_idempotent_binds_email_once(self):
		ci = self._catalog("cart-email-2")
		frappe.db.set_value("Catalog Item", ci, "published", 1, update_modified=False)
		lines = [{"catalog_item": ci, "qty": 1, "rate": 5}]
		frappe.set_user("Guest")
		try:
			out1 = create_guest_cart_web_order(
				company=self.company,
				idempotency_key="cart-email-key-2",
				lines=lines,
			)
			out2 = create_guest_cart_web_order(
				company=self.company,
				idempotency_key="cart-email-key-2",
				lines=lines,
				customer_email="late@example.com",
			)
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(out1["name"], out2["name"])
		self.assertEqual(out2.get("customer_email"), "late@example.com")

	def test_guest_cart_rejects_conflicting_email_on_retry(self):
		ci = self._catalog("cart-email-3")
		frappe.db.set_value("Catalog Item", ci, "published", 1, update_modified=False)
		lines = [{"catalog_item": ci, "qty": 1, "rate": 5}]
		frappe.set_user("Guest")
		try:
			create_guest_cart_web_order(
				company=self.company,
				idempotency_key="cart-email-key-3",
				lines=lines,
				customer_email="a@example.com",
			)
			with self.assertRaises(frappe.ValidationError):
				create_guest_cart_web_order(
					company=self.company,
					idempotency_key="cart-email-key-3",
					lines=lines,
					customer_email="b@example.com",
				)
		finally:
			frappe.set_user("Administrator")

	def test_guest_cart_rejects_unpublished_item(self):
		ci = self._catalog("cart-unpub")
		frappe.db.set_value("Catalog Item", ci, "published", 0, update_modified=False)
		lines = [{"catalog_item": ci, "qty": 1, "rate": 10}]
		frappe.set_user("Guest")
		try:
			with self.assertRaises(frappe.ValidationError):
				create_guest_cart_web_order(
					company=self.company,
					idempotency_key="cart-key-unpub",
					lines=lines,
				)
		finally:
			frappe.set_user("Administrator")

	def _ensure_tax_rule(self):
		if not frappe.db.exists("DocType", "Tax Rule"):
			return
		if frappe.db.exists("Tax Rule", {"company": self.company}):
			return
		from frappe.utils import add_years, today

		tax_gl = self._income_gl(number="8810", name="Web Checkout VAT")
		frappe.get_doc(
			{
				"doctype": "Tax Rule",
				"title": f"Default VAT {self.company}",
				"company": self.company,
				"valid_from": today(),
				"valid_to": add_years(today(), 5),
				"tax_type": "standard",
				"rate": 0,
				"account_head": tax_gl,
			}
		).insert(ignore_permissions=True)

	def test_guest_checkout_submit_creates_sales_invoice(self):
		self._income_gl()
		self._ensure_tax_rule()
		ci = self._catalog("checkout-sku")
		frappe.db.set_value("Catalog Item", ci, "published", 1, update_modified=False)
		lines = [{"catalog_item": ci, "qty": 1, "rate": 42}]
		checkout_key = f"checkout-idem-{frappe.generate_hash(length=6)}"
		frappe.set_user("Guest")
		try:
			cart = create_guest_cart_web_order(
				company=self.company,
				idempotency_key=checkout_key,
				lines=lines,
			)
			out = submit_guest_web_order(
				web_order=cart["name"],
				company=self.company,
				idempotency_key=checkout_key,
			)
			out2 = submit_guest_web_order(
				web_order=cart["name"],
				company=self.company,
				idempotency_key=checkout_key,
			)
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(out["docstatus"], 1)
		self.assertEqual(out2["docstatus"], 1)
		self.assertEqual(out["name"], out2["name"])
		self.assertTrue(out.get("sales_invoice"))
		self.assertEqual(out["status"], "Invoiced")
		pub = get_guest_web_order(web_order=cart["name"], company=self.company)
		self.assertEqual(pub["sales_invoice"], out["sales_invoice"])

	def test_guest_checkout_rejects_bad_idempotency_key(self):
		self._income_gl()
		ci = self._catalog("checkout-sku-2")
		frappe.db.set_value("Catalog Item", ci, "published", 1, update_modified=False)
		frappe.set_user("Guest")
		try:
			cart = create_guest_cart_web_order(
				company=self.company,
				idempotency_key="checkout-idem-2",
				lines=[{"catalog_item": ci, "qty": 1, "rate": 1}],
			)
			with self.assertRaises(frappe.ValidationError):
				submit_guest_web_order(
					web_order=cart["name"],
					company=self.company,
					idempotency_key="wrong-key",
				)
		finally:
			frappe.set_user("Administrator")

	def _bookable_resource(self, name="Room Guest API"):
		r = frappe.new_doc("Bookable Resource")
		r.company = self.company
		r.resource_name = name
		r.slot_duration_minutes = 60
		r.insert(ignore_permissions=True)
		return r.name

	def test_guest_list_bookable_resources(self):
		rn = self._bookable_resource("Res A")
		frappe.set_user("Guest")
		try:
			out = list_bookable_resources(company=self.company)
		finally:
			frappe.set_user("Administrator")
		names = {x["name"] for x in out["resources"]}
		self.assertIn(rn, names)

	def test_guest_booking_create_list_cancel(self):
		res = self._bookable_resource("Res B")
		start = now_datetime()
		end = add_to_date(start, hours=1)
		intent = self._create_payment_intent().name
		idem = f"bkg-1-{frappe.generate_hash(length=6)}"
		frappe.set_user("Guest")
		try:
			b1 = create_guest_booking(
				company=self.company,
				bookable_resource=res,
				start_datetime=start,
				end_datetime=end,
				customer_email="a@example.com",
				payment_intent=intent,
				idempotency_key=idem,
			)
			b1b = create_guest_booking(
				company=self.company,
				bookable_resource=res,
				start_datetime=start,
				end_datetime=end,
				customer_email="a@example.com",
				payment_intent=intent,
				idempotency_key=idem,
			)
			lst = list_confirmed_bookings_for_resource(
				company=self.company,
				bookable_resource=res,
				start=start.isoformat(),
				end=add_to_date(end, hours=2).isoformat(),
			)
			got = get_guest_booking(booking=b1["name"], company=self.company)
			cancelled = cancel_guest_booking(booking=b1["name"], company=self.company)
			cancelled2 = cancel_guest_booking(booking=b1["name"], company=self.company)
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(b1["name"], b1b["name"])
		self.assertEqual(b1["status"], "Confirmed")
		self.assertTrue(any(x["name"] == b1["name"] for x in lst["bookings"]))
		self.assertEqual(got["customer_email"], "a@example.com")
		self.assertEqual(cancelled["status"], "Cancelled")
		self.assertEqual(cancelled2["status"], "Cancelled")

	def test_guest_booking_overlap_rejected_on_create(self):
		res = self._bookable_resource("Res C")
		start = now_datetime()
		end = add_to_date(start, hours=1)
		intent = self._create_payment_intent().name
		frappe.set_user("Guest")
		try:
			create_guest_booking(
				company=self.company,
				bookable_resource=res,
				start_datetime=start,
				end_datetime=end,
				customer_email="overlap@example.com",
				payment_intent=intent,
				status="Confirmed",
			)
			with self.assertRaises(frappe.ValidationError):
				create_guest_booking(
					company=self.company,
					bookable_resource=res,
					start_datetime=add_to_date(start, minutes=30),
					end_datetime=add_to_date(end, minutes=30),
					customer_email="other@example.com",
					payment_intent=intent,
					status="Confirmed",
				)
		finally:
			frappe.set_user("Administrator")

	def test_guest_hold_then_confirm(self):
		res = self._bookable_resource("Res Hold")
		start = now_datetime()
		end = add_to_date(start, hours=1)
		intent = self._create_payment_intent().name
		frappe.set_user("Guest")
		try:
			h = create_guest_booking_hold(
				company=self.company,
				bookable_resource=res,
				start_datetime=start,
				end_datetime=end,
				customer_email="hold@example.com",
				idempotency_key="hold-idem-1",
				hold_ttl_minutes=30,
			)
			self.assertEqual(h["status"], "Draft")
			self.assertTrue(h.get("hold_expires_at"))
			c = confirm_guest_booking(
				booking=h["name"], company=self.company, payment_intent=intent
			)
			self.assertEqual(c["status"], "Confirmed")
			self.assertIsNone(c.get("hold_expires_at"))
			c2 = confirm_guest_booking(
				booking=h["name"], company=self.company, payment_intent=intent
			)
			self.assertEqual(c2["status"], "Confirmed")
		finally:
			frappe.set_user("Administrator")

	def test_guest_overlapping_hold_rejected(self):
		res = self._bookable_resource("Res Hold2")
		start = now_datetime()
		end = add_to_date(start, hours=1)
		frappe.set_user("Guest")
		try:
			create_guest_booking_hold(
				company=self.company,
				bookable_resource=res,
				start_datetime=start,
				end_datetime=end,
				hold_ttl_minutes=30,
			)
			with self.assertRaises(frappe.ValidationError):
				create_guest_booking_hold(
					company=self.company,
					bookable_resource=res,
					start_datetime=add_to_date(start, minutes=30),
					end_datetime=add_to_date(end, minutes=30),
					hold_ttl_minutes=30,
				)
		finally:
			frappe.set_user("Administrator")

	def test_guest_confirm_rejects_expired_hold(self):
		res = self._bookable_resource("Res Hold3")
		start = now_datetime()
		end = add_to_date(start, hours=1)
		frappe.set_user("Guest")
		try:
			h = create_guest_booking_hold(
				company=self.company,
				bookable_resource=res,
				start_datetime=start,
				end_datetime=end,
				hold_ttl_minutes=30,
			)
		finally:
			frappe.set_user("Administrator")
		frappe.db.set_value(
			"Booking",
			h["name"],
			"hold_expires_at",
			add_to_date(now_datetime(), hours=-1),
			update_modified=False,
		)
		frappe.set_user("Guest")
		try:
			with self.assertRaises(frappe.ValidationError):
				confirm_guest_booking(booking=h["name"], company=self.company)
		finally:
			frappe.set_user("Administrator")

	def _portal_token_setup(self, token: str):
		frappe.conf["omnexa_experience_portal_api_token"] = token

	def _portal_token_teardown(self):
		frappe.conf.pop("omnexa_experience_portal_api_token", None)

	def test_portal_me_list_orders_requires_bearer(self):
		self._portal_token_setup("portal-secret-1")
		try:
			ci = self._catalog("sku-portal-me")
			wo = frappe.new_doc("Web Order")
			wo.company = self.company
			wo.customer_email = "portal-list-unique@example.com"
			wo.append("lines", {"catalog_item": ci, "qty": 1, "rate": 10})
			wo.insert(ignore_permissions=True)
			with patch.object(frappe, "get_request_header", return_value=None):
				with self.assertRaises(frappe.PermissionError):
					list_my_web_orders(
						company=self.company, customer_email="portal-list-unique@example.com"
					)
			with patch.object(frappe, "get_request_header", return_value="Bearer wrong"):
				with self.assertRaises(frappe.PermissionError):
					list_my_web_orders(
						company=self.company, customer_email="portal-list-unique@example.com"
					)
			with patch.object(frappe, "get_request_header", return_value="Bearer portal-secret-1"):
				out = list_my_web_orders(
					company=self.company, customer_email="Portal-List-Unique@Example.com"
				)
			self.assertEqual(len(out["orders"]), 1)
			self.assertEqual(out["orders"][0]["name"], wo.name)
		finally:
			self._portal_token_teardown()

	def test_portal_me_get_order_wrong_email(self):
		self._portal_token_setup("portal-secret-2")
		try:
			ci = self._catalog("sku-portal-me-2")
			wo = frappe.new_doc("Web Order")
			wo.company = self.company
			wo.customer_email = "a@example.com"
			wo.append("lines", {"catalog_item": ci, "qty": 1, "rate": 1})
			wo.insert(ignore_permissions=True)
			with patch.object(frappe, "get_request_header", return_value="Bearer portal-secret-2"):
				with self.assertRaises(frappe.DoesNotExistError):
					get_my_web_order(
						web_order=wo.name,
						company=self.company,
						customer_email="b@example.com",
					)
		finally:
			self._portal_token_teardown()

	def test_portal_me_list_bookings(self):
		self._portal_token_setup("portal-secret-3")
		try:
			res = self._bookable_resource("Res Portal Me")
			start = add_to_date(now_datetime(), days=1, as_datetime=True)
			end = add_to_date(start, hours=2, as_datetime=True)
			intent = self._create_payment_intent()
			b = frappe.new_doc("Booking")
			b.company = self.company
			b.bookable_resource = res
			b.start_datetime = start
			b.end_datetime = end
			b.customer_email = "booker@example.com"
			b.payment_intent = intent.name
			b.status = "Confirmed"
			b.insert(ignore_permissions=True)
			with patch.object(frappe, "get_request_header", return_value="Bearer portal-secret-3"):
				out = list_my_bookings(company=self.company, customer_email="booker@example.com")
			names = {r["name"] for r in out["bookings"]}
			self.assertIn(b.name, names)
		finally:
			self._portal_token_teardown()

	def test_portal_me_get_booking_wrong_email(self):
		self._portal_token_setup("portal-secret-4")
		try:
			res = self._bookable_resource("Res Portal Me Detail")
			start = add_to_date(now_datetime(), days=2, as_datetime=True)
			end = add_to_date(start, hours=1, as_datetime=True)
			intent = self._create_payment_intent()
			b = frappe.new_doc("Booking")
			b.company = self.company
			b.bookable_resource = res
			b.start_datetime = start
			b.end_datetime = end
			b.customer_email = "owner@example.com"
			b.payment_intent = intent.name
			b.status = "Confirmed"
			b.insert(ignore_permissions=True)
			with patch.object(frappe, "get_request_header", return_value="Bearer portal-secret-4"):
				with self.assertRaises(frappe.DoesNotExistError):
					get_my_booking(
						booking=b.name,
						company=self.company,
						customer_email="other@example.com",
					)
				row = get_my_booking(
					booking=b.name,
					company=self.company,
					customer_email="Owner@Example.com",
				)
			self.assertEqual(row["name"], b.name)
			self.assertEqual(row["status"], "Confirmed")
		finally:
			self._portal_token_teardown()

	def test_experience_tenant_theme_rejects_bad_hex(self):
		t = frappe.new_doc("Experience Tenant Theme")
		t.company = self.company
		t.primary_color = "not-a-color"
		with self.assertRaises(frappe.ValidationError):
			t.insert(ignore_permissions=True)

	def test_experience_tenant_theme_rejects_low_primary_contrast(self):
		company_c = create_test_company("OMNX-EXP-CONT")
		t = frappe.new_doc("Experience Tenant Theme")
		t.company = company_c
		t.primary_color = "#777777"
		t.primary_contrast = "#888888"
		with self.assertRaises(frappe.ValidationError):
			t.insert(ignore_permissions=True)

	def test_experience_tenant_theme_accepts_strong_primary_contrast(self):
		company_c = create_test_company("OMNX-EXP-CONT2")
		t = frappe.new_doc("Experience Tenant Theme")
		t.company = company_c
		t.primary_color = "#2563eb"
		t.primary_contrast = "#ffffff"
		t.insert(ignore_permissions=True)
		self.assertEqual(t.primary_color, "#2563eb")

	def test_experience_tenant_theme_single_active_and_head_inject(self):
		company_b = create_test_company("OMNX-EXP-THEME")
		for nm in frappe.get_all("Experience Tenant Theme", pluck="name"):
			frappe.delete_doc("Experience Tenant Theme", nm, force=True, ignore_permissions=True)
		a = frappe.new_doc("Experience Tenant Theme")
		a.company = self.company
		a.apply_to_public_site = 1
		a.primary_color = "#112233"
		a.insert(ignore_permissions=True)
		b = frappe.new_doc("Experience Tenant Theme")
		b.company = company_b
		b.apply_to_public_site = 1
		b.primary_color = "#445566"
		b.insert(ignore_permissions=True)
		try:
			a.reload()
			self.assertEqual(a.apply_to_public_site, 0)
			out = update_website_context({})
			self.assertIn(HEAD_MARKER, out.get("head_html", ""))
			self.assertIn("omnexa-experience-tenant-theme", out.get("head_html", ""))
			self.assertIn("--ox-primary: #445566", out["head_html"])
		finally:
			frappe.delete_doc("Experience Tenant Theme", b.name, force=True, ignore_permissions=True)
			frappe.delete_doc("Experience Tenant Theme", a.name, force=True, ignore_permissions=True)

	def test_experience_tenant_theme_rejects_bad_asset_url(self):
		company_c = create_test_company("OMNX-BADURL")
		t = frappe.new_doc("Experience Tenant Theme")
		t.company = company_c
		t.favicon_url = "javascript:alert(1)"
		with self.assertRaises(frappe.ValidationError):
			t.insert(ignore_permissions=True)

	def test_experience_tenant_theme_favicon_only_inject(self):
		for nm in frappe.get_all("Experience Tenant Theme", pluck="name"):
			frappe.delete_doc("Experience Tenant Theme", nm, force=True, ignore_permissions=True)
		company_c = create_test_company("OMNX-FAVICO")
		t = frappe.new_doc("Experience Tenant Theme")
		t.company = company_c
		t.apply_to_public_site = 1
		t.favicon_url = "https://example.com/favicon.ico"
		t.insert(ignore_permissions=True)
		try:
			out = update_website_context({})
			h = out.get("head_html", "")
			self.assertIn(HEAD_MARKER, h)
			self.assertIn('rel="icon"', h)
			self.assertIn("https://example.com/favicon.ico", h)
			self.assertIn("omnexa-experience-tenant-theme", h)
			self.assertIn("--ox-primary: #2563eb", h)
		finally:
			frappe.delete_doc("Experience Tenant Theme", t.name, force=True, ignore_permissions=True)

	def test_experience_tenant_theme_attach_logo_and_favicon_inject(self):
		for nm in frappe.get_all("Experience Tenant Theme", pluck="name"):
			frappe.delete_doc("Experience Tenant Theme", nm, force=True, ignore_permissions=True)
		company_c = create_test_company("OMNX-ATTACH")
		t = frappe.new_doc("Experience Tenant Theme")
		t.company = company_c
		t.apply_to_public_site = 1
		t.primary_color = "#112233"
		t.primary_contrast = "#ffffff"
		# Simulate Attach URL values (files already hosted by site)
		t.logo = "/files/logo.png"
		t.favicon = "/files/favicon.ico"
		t.insert(ignore_permissions=True)
		try:
			out = update_website_context({})
			h = out.get("head_html", "")
			self.assertIn("/files/favicon.ico", h)
			self.assertIn("/files/logo.png", h)
			self.assertIn("--ox-logo-url", h)
		finally:
			frappe.delete_doc("Experience Tenant Theme", t.name, force=True, ignore_permissions=True)

	def test_experience_tenant_theme_preview_head(self):
		company_c = create_test_company("OMNX-PREVIEW")
		t = frappe.new_doc("Experience Tenant Theme")
		t.company = company_c
		t.primary_color = "#112233"
		t.primary_contrast = "#ffffff"
		t.favicon_url = "https://example.com/preview.ico"
		t.insert(ignore_permissions=True)
		try:
			out = preview_theme_head(theme=t.name, company=company_c)
			self.assertEqual(out["theme"], t.name)
			self.assertEqual(out["company"], company_c)
			self.assertIn(HEAD_MARKER, out["head_html"])
			self.assertIn("omnexa-experience-tenant-theme", out["head_html"])
			self.assertIn("rel=\"icon\"", out["head_html"])
			self.assertTrue(out["has_tokens"])
			self.assertTrue(out["has_brand_assets"])
		finally:
			frappe.delete_doc("Experience Tenant Theme", t.name, force=True, ignore_permissions=True)

	def test_experience_tenant_theme_preview_rejects_wrong_company(self):
		company_c = create_test_company("OMNX-PREVIEW2")
		t = frappe.new_doc("Experience Tenant Theme")
		t.company = company_c
		t.primary_color = "#223344"
		t.primary_contrast = "#ffffff"
		t.insert(ignore_permissions=True)
		try:
			with self.assertRaises(frappe.ValidationError):
				preview_theme_head(theme=t.name, company=self.company)
		finally:
			frappe.delete_doc("Experience Tenant Theme", t.name, force=True, ignore_permissions=True)

	def test_experience_tenant_theme_public_preview_token_flow(self):
		company_c = create_test_company("OMNX-PUBPREV")
		t = frappe.new_doc("Experience Tenant Theme")
		t.company = company_c
		t.primary_color = "#112233"
		t.primary_contrast = "#ffffff"
		t.insert(ignore_permissions=True)
		try:
			# Create token as admin (not Guest).
			prev = create_theme_preview_token(theme=t.name, company=company_c)
			self.assertTrue(prev.get("token"))

			# Simulate a web request with query params.
			frappe.form_dict = {
				"ox_theme_preview": t.name,
				"ox_preview_token": prev["token"],
			}
			before_request_theme_preview()

			out = update_website_context({})
			self.assertIn(HEAD_MARKER, out.get("head_html", ""))
			self.assertIn("--ox-primary: #112233", out["head_html"])
		finally:
			frappe.form_dict = {}
			if getattr(frappe.local, "flags", None):
				frappe.local.flags.pop("omnexa_experience_theme_preview_row", None)
			frappe.delete_doc("Experience Tenant Theme", t.name, force=True, ignore_permissions=True)

	def test_theme_publish_and_history(self):
		company_c = create_test_company("OMNX-PUBHIST")
		a = frappe.new_doc("Experience Tenant Theme")
		a.company = company_c
		a.primary_color = "#112233"
		a.primary_contrast = "#ffffff"
		a.insert(ignore_permissions=True)
		try:
			pub = publish_theme(theme=a.name, company=company_c, note="initial publish")
			self.assertEqual(pub["theme"], a.name)
			a.reload()
			self.assertEqual(a.apply_to_public_site, 1)
			self.assertTrue(a.published_at)
			h = list_theme_publish_history(company=company_c)
			self.assertGreaterEqual(len(h["history"]), 1)
			self.assertEqual(h["history"][0]["name"], a.name)
		finally:
			frappe.delete_doc("Experience Tenant Theme", a.name, force=True, ignore_permissions=True)

	def test_theme_rollback_to_previous(self):
		company_c = create_test_company("OMNX-ROLLBACK")
		a = frappe.new_doc("Experience Tenant Theme")
		a.company = company_c
		a.primary_color = "#112233"
		a.primary_contrast = "#ffffff"
		a.insert(ignore_permissions=True)
		b = frappe.new_doc("Experience Tenant Theme")
		b.company = company_c
		b.primary_color = "#223344"
		b.primary_contrast = "#ffffff"
		b.insert(ignore_permissions=True)
		try:
			publish_theme(theme=a.name, company=company_c, note="v1")
			publish_theme(theme=b.name, company=company_c, note="v2")
			out = rollback_theme(company=company_c, note="rollback to previous")
			self.assertEqual(out["theme"], a.name)
			a.reload()
			b.reload()
			self.assertEqual(a.apply_to_public_site, 1)
			self.assertEqual(b.apply_to_public_site, 0)
		finally:
			frappe.delete_doc("Experience Tenant Theme", b.name, force=True, ignore_permissions=True)
			frappe.delete_doc("Experience Tenant Theme", a.name, force=True, ignore_permissions=True)

	def test_theme_rollback_to_specific_theme(self):
		company_c = create_test_company("OMNX-ROLLTO")
		a = frappe.new_doc("Experience Tenant Theme")
		a.company = company_c
		a.primary_color = "#101010"
		a.primary_contrast = "#ffffff"
		a.insert(ignore_permissions=True)
		b = frappe.new_doc("Experience Tenant Theme")
		b.company = company_c
		b.primary_color = "#202020"
		b.primary_contrast = "#ffffff"
		b.insert(ignore_permissions=True)
		try:
			publish_theme(theme=a.name, company=company_c, note="v1")
			publish_theme(theme=b.name, company=company_c, note="v2")
			out = rollback_theme_to(theme=a.name, company=company_c, note="explicit rollback")
			self.assertEqual(out["theme"], a.name)
			a.reload()
			b.reload()
			self.assertEqual(a.apply_to_public_site, 1)
			self.assertEqual(b.apply_to_public_site, 0)
		finally:
			frappe.delete_doc("Experience Tenant Theme", b.name, force=True, ignore_permissions=True)
			frappe.delete_doc("Experience Tenant Theme", a.name, force=True, ignore_permissions=True)

	def test_theme_compare_versions(self):
		company_c = create_test_company("OMNX-CMP")
		a = frappe.new_doc("Experience Tenant Theme")
		a.company = company_c
		a.primary_color = "#101010"
		a.primary_contrast = "#ffffff"
		a.insert(ignore_permissions=True)
		b = frappe.new_doc("Experience Tenant Theme")
		b.company = company_c
		b.primary_color = "#202020"
		b.primary_contrast = "#ffffff"
		b.font_stack_for_web = "Arial, sans-serif"
		b.insert(ignore_permissions=True)
		try:
			out = compare_themes(theme_a=a.name, theme_b=b.name, company=company_c)
			self.assertEqual(out["theme_a"]["name"], a.name)
			self.assertEqual(out["theme_b"]["name"], b.name)
			self.assertGreaterEqual(out["diff_count"], 1)
			fields = {d["field"] for d in out["diffs"]}
			self.assertIn("primary_color", fields)
		finally:
			frappe.delete_doc("Experience Tenant Theme", b.name, force=True, ignore_permissions=True)
			frappe.delete_doc("Experience Tenant Theme", a.name, force=True, ignore_permissions=True)

	def test_desk_theme_payload_uses_erpgenex_theme_0426_defaults(self):
		company_c = create_test_company("OMNX-DESKTHEME")
		t = frappe.new_doc("Experience Tenant Theme")
		t.company = company_c
		t.theme_preset = "erpgenex_theme_0426"
		t.apply_to_desk = 1
		t.insert(ignore_permissions=True)
		prev_user = frappe.session.user
		try:
			frappe.session.user = "Administrator"
			frappe.defaults.set_user_default("Company", company_c, user="Administrator")
			out = get_desk_theme_payload()
			self.assertTrue(out["ok"])
			self.assertEqual(out["theme"]["preset"], "erpgenex_theme_0426")
			self.assertEqual(out["theme"]["tokens"]["primary_color"], "#2563eb")
			self.assertEqual(out["theme"]["tokens"]["desk_base_font_size"], "16px")
		finally:
			frappe.session.user = prev_user
			frappe.delete_doc("Experience Tenant Theme", t.name, force=True, ignore_permissions=True)
