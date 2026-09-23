import frappe

def after_install():
	load_departments()
	load_expense_categories()
	load_settings()
	frappe.msgprint("Spendgate installed successfully. Default departments, expense categories, and settings are ready.")


def load_departments():
	departments =[
		"Marketing",
		"Travel & Client Entertainment",
		"Equipment & Software",
		"Training",
	]
	for name in departments:
		if not frappe.db.exists("Department", name):
			frappe.get_doc(
				{
					"doctype": "Department",
					"department_name": name,
				}
			).insert(ignore_permissions=True)
def load_expense_categories():
    categories = [
        "Travel",
        "Software & Equipment",
        "Client Entertainment",
        "Training"
    ]
    for category in categories:
        if not frappe.db.exists("Expense Category", category):
            doc =frappe.get_doc({
                "doctype": "Expense Category",
                "category_name": category
            })
            doc.insert(ignore_permissions=True)
def load_settings():
	if not frappe.db.get_value("Spendgate Settings", "Spendgate Settings", "name"):
		settings= frappe.get_single("Spendgate Settings")
		if frappe.session.user!="Guest":
			settings.finance_email=frappe.session.user
		else:
			settings.finance_email=""
		settings.low_budget_alert_threshold_percent = 90
		settings.fiscal_year_start_month = 1
		settings.save(ignore_permissions=True)