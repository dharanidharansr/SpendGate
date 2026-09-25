import frappe

@frappe.whitelist()
def notify_finance_of_new_claim(claim):
    settings = frappe.get_single("Spendgate Settings")
    finance_email = settings.finance_email
    if not finance_email:
        return
    claim_doc = frappe.get_doc("Expense Claim", claim)
    frappe.sendmail(
        recipients=finance_email,
        subject="YEAHHHHHHHHHHHHHHHHHHHHH",
        message=f"""
        <p>new expense record {claim_doc} is submitted by {frappe.session.user}<p>
        """,
        delayed=False
    )