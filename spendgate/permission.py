import frappe

@frappe.whitelist()
def get_permission_query_conditions(user=None):
    user = user or frappe.session.user
    roles = frappe.get_roles(user)
    if "SG Finance Manager" in roles or "System Manager" in roles:
        return ""
    if "SG Staff" in roles:
        return f"`tabExpense Claim`.employee = {frappe.db.escape(user)}"
    if "SG Department Head" in roles:
        department = frappe.get_value(
            "Department",
            {"department_head": user},
            "name"
        )
        if department:
            return f"`tabExpense Claim`.department = {frappe.db.escape(department)}"