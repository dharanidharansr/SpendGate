# Copyright (c) 2026, dharanidharansr and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Budget(Document):
	def validate(self):
		if self.total_allocated <= 0:
			frappe.throw("Total Allocated must be greater than 0.")

	def before_insert(self):
		existing_budget = frappe.db.exists(
			"Budget",
			{
				"department": self.department,
				"fiscal_year": self.fiscal_year,
				"fiscal_quarter": self.fiscal_quarter,
			},
		)

		if existing_budget:
			frappe.throw("A Budget already exists for Department, Fiscal Year & Fiscal Qurter")

