import base64
import re
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class PayslipWizard(models.TransientModel):
    _name = "payslip.wizard"

    months = fields.Selection(
        [("6_month", "6 Months"), ("1_year", "1 Year")], string="Duration"
    )
    date_from = fields.Date()
    date_to = fields.Date()
    custom_range = fields.Boolean()

    def send_payslips_by_mail(self):
        records = self.env["hr.employee"].browse(self.env.context.get("active_ids"))
        recs = []
        for rec in records:
            if rec.slip_ids:
                attach = None
                template_id = 0
                if self.date_from and self.date_to:
                    duration = rec.slip_ids.filtered(
                        lambda r: r.date_from >= self.date_from
                        and r.date_to <= self.date_to
                    )
                elif self.months == "6_month":
                    self.date_from = date.today() - relativedelta(months=6)
                    self.date_to = date.today()
                    duration = rec.slip_ids.filtered(
                        lambda r: r.date_from >= self.date_from
                        and r.date_to <= self.date_to
                    )
                else:
                    self.date_from = date.today() - relativedelta(months=12)
                    self.date_to = date.today()
                    duration = rec.slip_ids.filtered(
                        lambda r: r.date_from >= self.date_from
                        and r.date_to <= self.date_to
                    )
                if duration:
                    try:
                        template_id = int(
                            rec.env["ir.config_parameter"]
                            .sudo()
                            .get_param(
                                "send_payslips_by_email_ss.choose_mail_template_for_employee"
                            )
                        )
                    except ValueError:
                        template_id = False
                    pdf_bin, file_format = self.env[
                        "ir.actions.report"
                    ]._render_qweb_pdf(
                        "hr_payroll.report_payslip_lang", res_ids=duration.ids
                    )
                    pdf_name = re.sub(r"\W+", "", rec.name) + "_Payslip.pdf"
                    attach = self.env["ir.attachment"].create(
                        {
                            "name": pdf_name,
                            "datas": base64.b64encode(pdf_bin),
                            "res_id": rec.id,
                            "res_model": "hr.payslip",
                            "type": "binary",
                        }
                    )
                else:
                    recs.append(rec.name)
                    continue
                if not template_id:
                    raise UserError(_("Email Template must be selected in settings."))
                if attach:
                    template_data = {"attachment_ids": attach.ids}
                    template = template_id and rec.env["mail.template"].browse(
                        template_id
                    )
                    template.send_mail(
                        rec.id, force_send=True, email_values=template_data
                    )
        if recs:
            rec = ",".join(recs)
            message = f"{rec} has no payslip on this duration"
            self.env["bus.bus"]._sendone(
                self.env.user.partner_id,
                "simple_notification",
                {"title": _("Notification"), "message": message, "sticky": False},
            )
