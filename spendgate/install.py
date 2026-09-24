import frappe

def after_install():
	departments = [
        'Travel',
        'Software & Equipment',
        'Client Entertainment',
        'Training'
    ]
	expense_categories = [
        'Travel',
        'Software & Equipment',
        'Client Entertainment',
        'Training'
    ]
	for department in departments:
		if not frappe.exists("Department", department):
			doc = frappe.get_doc("Department", department, ignore_permissions = True)
			doc.insert()
	for expense_category in expense_categories:
		if not frappe.exists("Expense Category", expense_category):
			doc = frappe.get_doc("Expense Category", expense_category, ignore_permissions = True)
			doc.insert()
	load_settings()
	frappe.msgprint("Spendgate installed successfully. Default departments, expense categories, and settings are ready.")

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