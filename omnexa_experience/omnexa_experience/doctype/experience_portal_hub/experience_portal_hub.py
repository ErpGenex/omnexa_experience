# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.model.document import Document
from frappe.utils import cstr


class ExperiencePortalHub(Document):
	def validate(self):
		self._normalize_slug()
		self._validate_branch()

	def _normalize_slug(self):
		if not self.site_slug and self.company:
			self.site_slug = frappe.scrub(self.company).replace("_", "-")[:60]
		if self.site_slug:
			self.site_slug = cstr(self.site_slug).strip().lower().replace(" ", "-")

	def _validate_branch(self):
		if self.default_branch and frappe.db.get_value("Branch", self.default_branch, "company") != self.company:
			frappe.throw("Default branch does not belong to the selected company.")
