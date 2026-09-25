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
def reassign_claim_department(claim, to_dept):
    if not claim:
        frappe.throw("Claim is required")
    if not to_dept:
        frappe.throw("New Department is required")
    if not frappe.db.exists("Expense Claim", claim):
        frappe.throw(f"Expense Claim '{claim}' does not exist")
    if not frappe.db.exists("Department", to_dept):
        frappe.throw(f"Department '{to_dept}' does not exist")
    expense_claim = frappe.get_doc("Expense Claim", claim)
    if expense_claim.status != "Draft":
        frappe.throw("Only Draft claims can be reassigned")
    if expense_claim.department == to_dept:
        frappe.throw("Claim is already assigned to this department")
    frappe.db.set_value(
        "Expense Claim",
        claim,
        "department",
        to_dept
    )
    frappe.db.commit()
    return {
        "success": True,
        "claim": claim,
        "department": to_dept
    }

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

@frappe.whitelist()
def get_budget_status(budget):
    if not frappe.db.exists("Budget", budget):
        frappe.throw("Budget does not exist")
    total = frappe.db.get_value("Budget", budget, "total_allocated") or 0
    spent = frappe.db.sql("""
        SELECT COALESCE(SUM(total_amount), 0) FROM `tabExpense Claim`
        WHERE budget = %s AND docstatus = 1
    """, (budget,))[0][0]
    return {"total_allocated": total, "spent": spent, "remaining": total - spent}


@frappe.whitelist()
def approve_claim(claim):
    doc = frappe.get_doc("Expense Claim", claim)
    doc.check_permission("write")
    if doc.status != "Pending Approval":
        frappe.throw("Only Pending Approval claims can be approved")
    frappe.db.set_value("Expense Claim", claim, {
        "status": "Approved",
        "approved_by": frappe.session.user,
    })
    frappe.enqueue("spendgate.notification.notify_finance_of_new_claim",claim=claim,queue="short")
    frappe.db.commit()
    return {"name": claim, "status": "Approved"}


@frappe.whitelist()
def reject_claim(claim, reason):
    if not (reason or "").strip():
        frappe.throw("Rejection reason is required")
    doc = frappe.get_doc("Expense Claim", claim)
    doc.check_permission("write")
    frappe.db.set_value("Expense Claim", claim, {
        "status": "Rejected",
        "rejection_reason": reason,
    })
    frappe.db.commit()
    return {"name": claim, "status": "Rejected"}