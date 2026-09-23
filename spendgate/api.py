import frappe
from frappe.query_builder import DocType

@frappe.whitelist()
def get_claims_pending_approval():
    EC = DocType("Expense Claim")
    result = (
        frappe.qb.from_(EC)
        .select(EC.name, EC.employee, EC.department, EC.total_amount, EC.expense_date)
        .where(EC.status.eq("Pending Approval"))
        .orderby(EC.expense_date)
        .run(as_dict=True)
    )
    return result

@frappe.whitelist()
def reassign_department_claims(from_dept, to_dept):
    if not frappe.db.exists("Department", from_dept):
        frappe.throw(f"Department '{from_dept}' does not exist")
    if not frappe.db.exists("Department", to_dept):
        frappe.throw(f"Department '{to_dept}' does not exist")
    try:
        frappe.db.sql(
            """
            UPDATE `tabExpense Claim`
            SET department = %s
            WHERE department = %s AND docstatus = 0
            """,
            (to_dept, from_dept),
        )
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            title="reassign_department_claims failed",
            message=frappe.get_traceback(),
        )
        raise

@frappe.whitelist()
def share_expense_claim(claim_name, user_email):
    if not frappe.db.exists("Expense Claim", claim_name):
        frappe.throw("Expense Claim does not exist")
    if not frappe.db.exists("User", user_email):
        frappe.throw("User does not exist")
    frappe.has_permission("Expense Claim", ptype="share", doc=claim_name, throw=True)
    share_doc = frappe.share.add("Expense Claim",
        claim_name,
        user=user_email,
        read=1,
        write=0,
        submit=0,
        notify=1)
    return {"share_name": share_doc.name, "user": share_doc.user}


@frappe.whitelist()
def get_expense_claim_data_unsafe(claim_name):
    doc = frappe.get_doc("Expense Claim", claim_name, ignore_permissions=True)
    return doc.as_dict()


@frappe.whitelist()
def get_expense_claim_data_safe(claim_name):
    claims = frappe.get_list(
        "Expense Claim",
        filters={"name": claim_name},
        fields=[
            "name",
            "employee",
            "department",
            "total_amount",
            "status",
            "expense_date",
            "description",
        ],
        limit_page_length=1,
    )
    if not claims:
        frappe.throw(
            "Not found or no permission",
            frappe.PermissionError,
        )

    claim = claims[0]
    user = frappe.session.user
    roles = frappe.get_roles(user)

    inside_department = bool(
        "System Manager" in roles
        or "SG Finance Manager" in roles
        or claim["employee"] == user
        or frappe.db.exists(
            "Department",
            {"name": claim["department"], "department_head": user},
        )
    )

    if inside_department:
        line_items = frappe.get_all(
            "Expense Line",
            filters={"parent": claim_name, "parenttype": "Expense Claim"},
            fields=["category", "vendor", "amount", "notes", "idx"],
        )
    else:
        line_items = frappe.get_all(
            "Expense Line",
            filters={"parent": claim_name, "parenttype": "Expense Claim"},
            fields=["category", "vendor", "notes", "idx"],
        )

    claim["expense_lines"] = line_items
    claim["amounts_visible"] = inside_department
    return claim
