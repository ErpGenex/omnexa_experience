# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_experience.omnexa_experience.activity_sites import activity_site_path
from omnexa_experience.omnexa_experience.activity_website_registry import (
	get_activity_website_pack,
	list_installed_activity_websites,
	resolve_legacy_redirect,
)


class TestActivityWebsiteRegistry(FrappeTestCase):
	def test_education_pack_registered_when_app_installed(self):
		if "omnexa_education" not in frappe.get_installed_apps():
			self.skipTest("omnexa_education not installed")
		pack = get_activity_website_pack("Education")
		self.assertIsNotNone(pack)
		self.assertEqual(pack["base_path"], "/education")
		self.assertEqual(pack["app"], "omnexa_education")

	def test_education_site_path_uses_app_pack(self):
		if "omnexa_education" not in frappe.get_installed_apps():
			self.skipTest("omnexa_education not installed")
		self.assertEqual(activity_site_path("Education"), "/education")

	def test_campus_legacy_redirect_to_education(self):
		if "omnexa_education" not in frappe.get_installed_apps():
			self.skipTest("omnexa_education not installed")
		self.assertEqual(resolve_legacy_redirect("/campus"), "/education")
		self.assertEqual(resolve_legacy_redirect("/campus/programs"), "/education/programs")
		self.assertEqual(resolve_legacy_redirect("/campus/apply"), "/education/apply")

	def test_healthcare_pack_when_installed(self):
		if "omnexa_healthcare" not in frappe.get_installed_apps():
			self.skipTest("omnexa_healthcare not installed")
		pack = get_activity_website_pack("Healthcare")
		self.assertIsNotNone(pack)
		self.assertEqual(pack["base_path"], "/hospital")

	def test_list_installed_websites(self):
		rows = list_installed_activity_websites()
		activities = {r["business_activity"] for r in rows}
		if "omnexa_education" in frappe.get_installed_apps():
			self.assertIn("Education", activities)
		if "omnexa_healthcare" in frappe.get_installed_apps():
			self.assertIn("Healthcare", activities)
