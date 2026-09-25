## B2c
Ans:
self.save() inside validate() causes recursion because save calls validate again
Also budget.total_allocated will be reduced again on every save, so cancellation or edits can make the value wrong
Correct:
def validate(self):
self.total_amount = sum(r.amount for r in self.expense_lines)
Use a live SUM query for spent instead of changing total_allocated
## B2d
Ans:
Yes, both can succeed
Both transaction can read the same spent_so_far before commit
There is currently no SELECT FOR UPDATE, GET_LOCK or SERIALIZABLE to stop this
## C3
Ans:
Yes. frappe.rename_doc() updates linked Link fields in Budgets and Expense Claims because department is a Link field
It will not happen for normal Data field
## D2
Ans:
frappe.get_all() skips permission checks, so a low privilege user may see other users/departments claims
Use frappe.get_list() instead
## E1
Ans:
self.save() inside on_update() calls on_update() again, causing an infinite loop and RecursionError
## E3
Ans:
I would use frappe.db.get_value() because only one field is needed. get_doc() loads the full document
threshold = frappe.db.get_value("SpendGate Settings", None, "low_budget_alert_threshold_percent")
## H1
Ans:
frappe.call() is async, so validate does not wait for the response
Fetch the data in onload/refresh and use the stored value in validate. Server should still check it
## I1
Ans:
Parameterized SQL is preferred because it prevents SQL injection