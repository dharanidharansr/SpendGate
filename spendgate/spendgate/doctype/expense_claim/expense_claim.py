# Copyright (c) 2026, dharanidharansr and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class ExpenseClaim(Document):
    def validate(self):
        self.calculate_total_amount()

    def before_save(self):
        budget_total = frappe.db.get_value("Budget", self.budget, "total_allocated")
        self.remaining_budget_at_submission = budget_total - self.total_amount

    def calculate_total_amount(self):
        total = 0

        for row in self.expense_lines:
            total += row.amount or 0

        self.total_amount = total