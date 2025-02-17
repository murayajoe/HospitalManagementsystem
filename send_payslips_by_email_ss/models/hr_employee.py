from odoo import _, models


class Employee(models.Model):
    _inherit = "hr.employee"

    def action_send_payslips(self):
        return {
            "name": _("Payslips"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_id": self.env.ref(
                "send_payslips_by_email_ss.view_payslip_wizard_form"
            ).id,
            "res_model": "payslip.wizard",
            "target": "new",
            "context": {"active_ids": self.ids},
        }
