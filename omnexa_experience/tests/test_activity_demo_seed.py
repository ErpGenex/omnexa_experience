# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_experience.omnexa_experience.activity_demo_seed import seed_company_activity_website


class TestActivityDemoSeed(FrappeTestCase):
	def setUp(self):
		companies = frappe.get_all("Company", pluck="name", limit=1)
		self.company = companies[0] if companies else None
		if not self.company:
			self.skipTest("No company")
		self.branch = frappe.db.get_value(
			"Branch",
			{"company": self.company},
			"name",
			order_by="is_head_office desc, creation asc",
		)
		if not self.branch:
			self.skipTest("No branch")

	def test_seed_trading_catalog(self):
		if not frappe.db.has_column("Company", "business_activity"):
			self.skipTest("No business_activity")
		frappe.db.set_value("Company", self.company, "business_activity", "Trading", update_modified=False)
		result = seed_company_activity_website(company=self.company, branch=self.branch, force=0)
		self.assertTrue(result.get("ok"))
		self.assertEqual(result["business_activity"], "Trading")
		self.assertTrue(result.get("site_url"))
		catalog = result.get("catalog") or {}
		self.assertGreaterEqual(catalog.get("count", 0), 1)
		frappe.db.set_value("Company", self.company, "business_activity", "Healthcare", update_modified=False)

	def test_seed_healthcare_when_installed(self):
		if "omnexa_healthcare" not in frappe.get_installed_apps():
			self.skipTest("Healthcare app not installed")
		if not frappe.db.has_column("Company", "business_activity"):
			self.skipTest("No business_activity")
		frappe.db.set_value("Company", self.company, "business_activity", "Healthcare", update_modified=False)
		result = seed_company_activity_website(
			company=self.company,
			branch=self.branch,
			force=0,
			patients=5,
		)
		self.assertTrue(result.get("ok"))
		self.assertIn("healthcare", result)
		self.assertIn("/hospital", result.get("site_url", ""))
