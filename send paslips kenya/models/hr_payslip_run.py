import base64
import re

from odoo import _, models
from odoo.exceptions import UserError


class HrPayslipRun(models.Model):
    _name = "hr.payslip.run"
    _inherit = ["hr.payslip.run", "mail.thread", "mail.activity.mixin"]

    def action_payslip_batch_send(self):
        for rec in self.slip_ids:
            try:
                template_id = int(
                    rec.env["ir.config_parameter"]
                    .sudo()
                    .get_param("send_payslips_by_email_ss.choose_mail_template")
                )
            except ValueError:
                template_id = False
            if not template_id:
                raise UserError(_("Email Template must be selected in settings."))
            pdf_bin, file_format = self.env["ir.actions.report"]._render_qweb_pdf(
                "hr_payroll.report_payslip_lang", res_ids=rec.ids
            )
            pdf_name = re.sub(r"\W+", "", rec.employee_id.name) + "_Payslip.pdf"
            attach = self.env["ir.attachment"].create(
                {
                    "name": pdf_name,
                    "datas": base64.b64encode(pdf_bin),
                    "res_id": rec.id,
                    "res_model": "hr.payslip",
                    "type": "binary",
                }
            )
            template_data = {"attachment_ids": attach.ids}
            template = template_id and rec.env["mail.template"].browse(template_id)
            template.send_mail(rec.id, force_send=True, email_values=template_data)
        message = "Mail sent"
        self.env["bus.bus"]._sendone(
            self.env.user.partner_id,
            "simple_notification",
            {"title": _("Notification"), "message": message, "sticky": False},
        )
