// Copyright (c) 2026, dharanidharansr and contributors
// For license information, please see license.txt

function get_fiscal_details(frm) {
    const date = frappe.datetime.str_to_obj(frm.doc.expense_date || frappe.datetime.get_today());
    return {
        fiscal_year: date.getFullYear(),
        fiscal_quarter: "Q" + Math.floor(date.getMonth() / 3 + 1)
    };
}
function set_budget_query(frm) {
    const fiscal = get_fiscal_details(frm);
    frm.set_query("budget", {
        filters: {
            department: frm.doc.department,
            fiscal_year: fiscal.fiscal_year,
            fiscal_quarter: fiscal.fiscal_quarter
        }
    });
}
function get_total(frm) {
    return (frm.doc.expense_lines || []).reduce((total, row) => total + flt(row.amount), 0);
}
function show_budget_status(frm) {
    if (!frm.doc.budget) {
        frm.budget_remaining = null;
        return;
    }
    frappe.call({
        method: "spendgate.api.get_budget_status",
        args: { budget: frm.doc.budget },
        callback: function(r) {
            if (!r.message) return;
            frm.budget_remaining = r.message.remaining;
            if (frm.dashboard) {
                frm.dashboard.clear_headline();
                frm.dashboard.add_indicator(
                    "Budget Remaining: " + frappe.format(frm.budget_remaining, { fieldtype: "Currency" }),
                    frm.budget_remaining >= 0 ? "green" : "red"
                );
            }
        }
    });
}
frappe.ui.form.on("Expense Claim", {
    setup: function(frm) {
        frm.budget_remaining = null;
    },
    refresh: function(frm) {
        set_budget_query(frm);

        if (frm.doc.status) {
            const colors = {
                Draft: "blue",
                "Pending Approval": "orange",
                Approved: "green",
                Rejected: "red",
                Reimbursed: "gray",
                Cancelled: "red"
            };

            frm.dashboard.add_indicator(frm.doc.status, colors[frm.doc.status] || "blue");
        }
        const roles = frappe.user_roles || [];
        const can_approve = roles.includes("SG Department Head") ||
            roles.includes("SG Finance Manager") ||
            roles.includes("System Manager");

        if (can_approve && frm.doc.status === "Pending Approval" && !frm.is_new()) {
            frm.add_custom_button("Approve", function() {
                frappe.call({
                    method: "spendgate.api.approve_claim",
                    args: { claim: frm.doc.name },
                    freeze: true,
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.show_alert({
                                message: "Claim approved",
                                indicator: "green"
                            });
                            frm.reload_doc();
                        }
                    }
                });
            }, "Actions");

            frm.add_custom_button("Reject", function() {
                const dialog = new frappe.ui.Dialog({
                    title: "Reject Claim",
                    fields: [
                        {
                            fieldtype: "Small Text",
                            label: "Rejection Reason",
                            fieldname: "reason",
                            reqd: 1
                        }
                    ],
                    primary_action_label: "Reject",
                    primary_action: function(values) {
                        dialog.hide();

                        frappe.call({
                            method: "spendgate.api.reject_claim",
                            args: {
                                claim: frm.doc.name,
                                reason: values.reason
                            },
                            freeze: true,
                            callback: function(r) {
                                if (!r.exc) {
                                    frappe.show_alert({
                                        message: "Claim rejected",
                                        indicator: "red"
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                });

                dialog.show();
            }, "Actions");
        }
        if (can_approve && !frm.is_new() && frm.doc.status === "Draft") {
            frm.add_custom_button("Reassign Department", function() {
                frappe.prompt({
                    label: "New Department",
                    fieldname: "to_dept",
                    fieldtype: "Link",
                    options: "Department",
                    reqd: 1
                }, function(values) {6
                    frappe.confirm(
                        `Reassign claim from <b>${frm.doc.department}</b> to <b>${values.to_dept}</b>?`,
                        function() {
                            frappe.call({
                                method: "spendgate.api.reassign_claim_department",
                                args: {
                                    claim: frm.doc.name,
                                    to_dept: values.to_dept
                                },
                                freeze: true,
                                callback: function(r) {
                                    if (!r.exc) {
                                        frappe.show_alert({
                                            message: "Department reassigned",
                                            indicator: "blue"
                                        });
                                        frm.reload_doc().then(function() {
                                            frm.trigger("department");
                                        });
                                    }
                                }
                            });
                        }
                    );
                }, "Reassign Department");
            }, "Actions");
        }
        show_budget_status(frm);
    },
    department: function(frm) {
        set_budget_query(frm);
        frm.set_value("budget", "");
        frm.budget_remaining = null;
    },
    budget: function(frm) {
        show_budget_status(frm);
    },
    expense_date: function(frm) {
        set_budget_query(frm);
        if (frm.doc.budget) show_budget_status(frm);
    },
    validate: function(frm) {
        if (frm.budget_remaining == null) return;
        const total = get_total(frm);
        if (total > frm.budget_remaining) {
            frappe.msgprint({
                title: "Over Budget",
                indicator: "orange",
                message: "Total " + frappe.format(total, { fieldtype: "Currency" }) +
                    " exceeds remaining budget " + frappe.format(frm.budget_remaining, { fieldtype: "Currency" })
            });
        }
    }
});
frappe.ui.form.on("Expense Line", {
    amount: function(frm) {
        const total = get_total(frm);
        frm.set_value("total_amount", total);

        if (frm.budget_remaining != null && total > frm.budget_remaining) {
            frappe.msgprint({
                title: "Over Budget",
                indicator: "orange",
                message: "Total " + frappe.format(total, { fieldtype: "Currency" }) +
                    " exceeds remaining budget " + frappe.format(frm.budget_remaining, { fieldtype: "Currency" })
            });
        }
    }
});