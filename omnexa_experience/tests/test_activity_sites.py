# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_experience.omnexa_experience.activity_site_api import get_activity_site_pack_api
from omnexa_experience.omnexa_experience.activity_sites import (
	activity_site_path,
	build_activity_site_url,
	resolve_public_site_url,
)
from omnexa_experience.omnexa_experience.public_portal import get_portal_config


class TestActivitySites(FrappeTestCase):
	def setUp(self):
		companies = frappe.get_all("Company", pluck="name", limit=1)
		self.company = companies[0] if companies else None
		if not self.company:
			self.skipTest("No company")
		if frappe.db.has_column("Company", "business_activity"):
			frappe.db.set_value("Company", self.company, "business_activity", "Trading", update_modified=False)
		if frappe.db.exists("Experience Portal Hub", self.company):
			frappe.db.set_value(
				"Experience Portal Hub",
				self.company,
				{"is_enabled": 1, "site_slug": "test-activity-site", "follow_company_activity": 1},
			)
		else:
			frappe.get_doc(
				{
					"doctype": "Experience Portal Hub",
					"company": self.company,
					"is_enabled": 1,
					"site_slug": "test-activity-site",
					"follow_company_activity": 1,
				}
			).insert(ignore_permissions=True)

	def tearDown(self):
		if self.company and frappe.db.has_column("Company", "business_activity"):
			frappe.db.set_value("Company", self.company, "business_activity", "Healthcare", update_modified=False)

	def test_activity_site_path_trading(self):
		self.assertEqual(activity_site_path("Trading"), "/store")

	def test_build_activity_site_url(self):
		url = build_activity_site_url(company=self.company, activity="Trading", site_slug="test-activity-site")
		self.assertIn("/store", url)
		self.assertIn("site=test-activity-site", url)

	def test_resolve_public_site_url(self):
		url = resolve_public_site_url(company=self.company)
		self.assertIn("/store", url)

	def test_portal_config_includes_activity_site(self):
		cfg = get_portal_config(company=self.company)
		self.assertIn("activity_site", cfg["urls"])
		self.assertIn("/store", cfg["urls"]["activity_site"])

	def test_activity_site_pack_api(self):
		pack = get_activity_site_pack_api(company=self.company)
		self.assertEqual(pack["business_activity"], "Trading")
		self.assertEqual(pack["base_path"], "/store")
		self.assertTrue(pack.get("hero_image"))
		self.assertTrue(pack.get("nav"))
		self.assertTrue(pack.get("testimonials"))
