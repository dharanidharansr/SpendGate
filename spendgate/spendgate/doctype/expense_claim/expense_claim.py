# Copyright (c) 2026, dharanidharansr and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document

class ExpenseClaim(Document):
    def validate(self):
        self.calculate_total_amount()
        budget_dept = frappe.db.get_value("Budget", self.budget, "department")
        if self.department != budget_dept:
            frappe.throw(f"Department '{self.department}' does not match Budget '{self.budget}' department '{budget_dept}'")

    def before_submit(self):
        budget_total = frappe.db.get_value("Budget", self.budget, "total_allocated")
        spent_so_far = frappe.db.sql("""
            SELECT COALESCE(SUM(total_amount), 0) FROM `tabExpense Claim`
            WHERE budget = %s AND docstatus = 1 AND name != %s
        """, (self.budget, self.name or ""))[0][0]
        projected = spent_so_far + self.total_amount
        if projected > budget_total:
            overage = projected - budget_total
            remaining = budget_total - spent_so_far
            frappe.throw(f"Budget exceeded for department '{self.department}': overage is {overage}, remaining budget is {remaining}")
        self._spent_so_far = spent_so_far

    def on_submit(self):
        budget_total = frappe.db.get_value("Budget", self.budget, "total_allocated")
        spent_so_far = frappe.db.sql("""
            SELECT COALESCE(SUM(total_amount), 0) FROM `tabExpense Claim`
            WHERE budget = %s AND docstatus = 1 AND name != %s
        """, (self.budget, self.name or ""))[0][0]
        remaining = budget_total - spent_so_far - self.total_amount
        updates = {"remaining_budget_at_submission": remaining}
        if not self.approved_by:
            updates["approved_by"] = frappe.session.user
        self.db_set(updates, update_modified=False)
        self.remaining_budget_at_submission = remaining
        if "approved_by" in updates:
            self.approved_by = frappe.session.user
        frappe.enqueue("spendgate.notification.notify_finance_of_new_claim",claim=self.name,queue="short")

    def on_cancel(self):
        if self.status == "Reimbursed":
            frappe.throw(
                "Cannot cancel a Reimbursed claim — money already paid out; "
                "use a reversal process instead."
            )
        self.db_set("status","Cancelled")
        self.status = "Cancelled"

    def on_trash(self):
        if self.status not in ("Cancelled", "Draft"):
            frappe.throw("Can't delete expense claim")

    def calculate_total_amount(self):
        total= 0
        for row in self.expense_lines:
            if row.amount<=0:
                frappe.throw("Amount must be greater than 0")
            else:
                total += row.amount
        self.total_amount = total
