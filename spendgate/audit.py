import frappe


def log_change(doc, action=None):
	if doc.doctype == "Audit Log":
		return
	if frappe.flags.in_migrate or frappe.flags.in_install or frappe.flags.in_uninstall:
		return
	frappe.get_doc(
		{
			"doctype": "Audit Log",
			"doctype_name": doc.doctype,
			"document_name": doc.name,
			"action": action,
			"user": frappe.session.user,
			"timestamp": frappe.utils.now_datetime(),
		}
	).insert(ignore_permissions=True)