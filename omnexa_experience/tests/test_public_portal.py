# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_experience.omnexa_experience.public_portal import build_portal_urls, get_portal_config


class TestPublicPortal(FrappeTestCase):
	def setUp(self):
		companies = frappe.get_all("Company", pluck="name", limit=1)
		self.company = companies[0] if companies else None
		if not self.company:
			self.skipTest("No company")
		if frappe.db.exists("Experience Portal Hub", self.company):
			frappe.db.set_value("Experience Portal Hub", self.company, {"is_enabled": 1, "site_slug": "test-portal"})
		else:
			frappe.get_doc(
				{
					"doctype": "Experience Portal Hub",
					"company": self.company,
					"is_enabled": 1,
					"site_slug": "test-portal",
				}
			).insert(ignore_permissions=True)

	def test_get_portal_config(self):
		cfg = get_portal_config(company=self.company)
		self.assertEqual(cfg["company"], self.company)
		self.assertIn("verticals", cfg)
		self.assertIn("sub_portals", cfg)

	def test_get_portal_config_by_site(self):
		cfg = get_portal_config(site="test-portal")
		self.assertEqual(cfg["company"], self.company)

	def test_build_portal_urls(self):
		urls = build_portal_urls(company=self.company, site_slug="test-portal")
		self.assertIn("/portal", urls["home"])
		self.assertIn("/portal/patient", urls["patient"])
