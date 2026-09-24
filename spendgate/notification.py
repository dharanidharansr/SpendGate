import frappe

@frappe.whitelist()
def notify_finance_of_new_claim(claim):
    settings = frappe.get_single("Spendgate Settings")
    finance_email = settings.finance_email
    if not finance_email:
        return
    claim_doc = frappe.get_doc("Expense Claim", claim)
    frappe.sendmail(
        recipients=[finance_email],
        subject=f"New Expense Claim {claim_doc.name}",
        message=(
            f"Claim {claim_doc.name} for {claim_doc.total_amount} "
            f"({claim_doc.department}) was submitted by {claim_doc.employee}."
        )
    )