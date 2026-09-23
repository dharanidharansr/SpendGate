// Copyright (c) 2026, dharanidharansr and contributors
// For license information, please see license.txt
// function total_amount_cal(frm,cdt,cdn){
//     let t=0
//     let r=locals[cdt][cdn]
//     (frm.doc.expense_lines||[]).forEach(r => {
//         t=t+r.amount || 0
//     });
//     frm.set_value("total_amount",t);
// }
frappe.ui.form.on("Expense Claim", {
    refresh(frm, cdt, cdn) {
        // total_amount_cal(frm, cdt, cdn);
        frm.set_query("budget", function() {
            return {
                filters: {
                    department: frm.doc.department
                }
            };
        });
    },
    department(frm) {
        frm.set_query("budget", function() {
            return {
                filters: {
                    department: frm.doc.department
                }
            };
        });
        frm.doc.budget = "";
        frm.refresh_field("budget");
    }
});