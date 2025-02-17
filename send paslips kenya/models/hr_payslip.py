import base64
import re

from odoo import _, fields, models
from odoo.exceptions import UserError


class HRPayslip(models.Model):
    _name = "hr.payslip"
    _inherit = ["hr.payslip", "mail.thread", "mail.activity.mixin"]

    def payslip_send_mail(self):
        self.ensure_one()
        try:
            template_id = int(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("send_payslips_by_email_ss.choose_mail_template")
            )
        except ValueError:
            template_id = False
        if not template_id:
            raise UserError(_("Email Template must be selected in settings."))
        template = template_id and self.env["mail.template"].browse(template_id)
        pdf_bin, file_format = self.env["ir.actions.report"]._render_qweb_pdf(
            "hr_payroll.report_payslip_lang", res_ids=self.ids
        )
        pdf_name = re.sub(r"\W+", "", self.employee_id.name) + "_Payslip.pdf"
        attach = self.env["ir.attachment"].create(
            {
                "name": pdf_name,
                "datas": base64.b64encode(pdf_bin),
                "res_id": self.id,
                "res_model": "hr.payslip",
                "type": "binary",
            }
        )
        template_data = {"attachment_ids": attach.ids}
        template.send_mail(self.id, force_send=True, email_values=template_data)
        message = "Mail sent"
        self.env["bus.bus"]._sendone(
            self.env.user.partner_id,
            "simple_notification",
            {"title": _("Notification"), "message": message, "sticky": False},
        )

    def send_payslip_by_email_action(self):
        for rec in self:
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
            template = template_id and rec.env["mail.template"].browse(template_id)
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
            template.send_mail(rec.id, force_send=True, email_values=template_data)
        message = "Mail sent"
        self.env["bus.bus"]._sendone(
            self.env.user.partner_id,
            "simple_notification",
            {"title": _("Notification"), "message": message, "sticky": False},
        )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    choose_mail_template = fields.Many2one(
        "mail.template",
        string="Mail Template For Payroll",
        config_parameter="send_payslips_by_email_ss.choose_mail_template",
    )

    choose_mail_template_for_employee = fields.Many2one(
        "mail.template",
        string="Mail Template For Employee",
        config_parameter="send_payslips_by_email_ss.choose_mail_template_for_employee",
    )
