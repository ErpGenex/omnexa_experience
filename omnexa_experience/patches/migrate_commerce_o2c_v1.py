# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Normalize legacy commerce O2C data after status / channel schema upgrade."""

import frappe


def execute():
	frappe.db.sql(
		"UPDATE `tabWeb Order` SET `status` = %s WHERE `status` = %s",
		("Invoiced", "Confirmed"),
	)
	frappe.db.sql(
		"UPDATE `tabWeb Order` SET `order_channel` = %s WHERE IFNULL(`order_channel`, '') = ''",
		("offline_web",),
	)
	frappe.db.commit()
