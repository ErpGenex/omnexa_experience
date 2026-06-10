# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_experience.omnexa_experience.portal_registry import (
	get_company_business_activity,
	list_active_sub_portals,
	list_active_verticals,
)
from omnexa_experience.omnexa_experience.public_portal import build_portal_urls, get_portal_config


class TestPublicPortal(FrappeTestCase):
	def setUp(self):
		companies = frappe.get_all("Company", pluck="name", limit=1)
		self.company = companies[0] if companies else None
		if not self.company:
			self.skipTest("No company")
		if frappe.db.has_column("Company", "business_activity"):
			frappe.db.set_value("Company", self.company, "business_activity", "Healthcare", update_modified=False)
		if frappe.db.exists("Experience Portal Hub", self.company):
			frappe.db.set_value(
				"Experience Portal Hub",
				self.company,
				{"is_enabled": 1, "site_slug": "test-portal", "follow_company_activity": 1},
			)
		else:
			frappe.get_doc(
				{
					"doctype": "Experience Portal Hub",
					"company": self.company,
					"is_enabled": 1,
					"site_slug": "test-portal",
					"follow_company_activity": 1,
				}
			).insert(ignore_permissions=True)

	def test_get_portal_config(self):
		cfg = get_portal_config(company=self.company)
		self.assertEqual(cfg["company"], self.company)
		self.assertEqual(cfg["business_activity"], "Healthcare")
		self.assertEqual(cfg["layout_mode"], "single_activity")
		self.assertLessEqual(len(cfg["verticals"]), 2)

	def test_get_portal_config_by_site(self):
		cfg = get_portal_config(site="test-portal")
		self.assertEqual(cfg["company"], self.company)

	def test_get_portal_config_without_params(self):
		cfg = get_portal_config()
		self.assertEqual(cfg["company"], self.company)

	def test_verticals_scoped_to_company_activity(self):
		hub = frappe.get_doc("Experience Portal Hub", self.company)
		verticals = list_active_verticals(hub)
		ids = {v["id"] for v in verticals}
		if "omnexa_healthcare" in frappe.get_installed_apps():
			self.assertIn("healthcare", ids)
		self.assertNotIn("trading", ids)

	def test_trading_company_shows_trading_only(self):
		if not frappe.db.has_column("Company", "business_activity"):
			self.skipTest("No business_activity column")
		frappe.db.set_value("Company", self.company, "business_activity", "Trading", update_modified=False)
		hub = frappe.get_doc("Experience Portal Hub", self.company)
		ids = {v["id"] for v in list_active_verticals(hub)}
		if "omnexa_trading" in frappe.get_installed_apps():
			self.assertIn("trading", ids)
		self.assertNotIn("healthcare", ids)
		frappe.db.set_value("Company", self.company, "business_activity", "Healthcare", update_modified=False)

	def test_build_portal_urls(self):
		urls = build_portal_urls(company=self.company, site_slug="test-portal")
		self.assertIn("/portal", urls["home"])
		self.assertIn("/portal/patient", urls["patient"])

	def test_get_company_business_activity(self):
		self.assertEqual(get_company_business_activity(self.company), "Healthcare")
