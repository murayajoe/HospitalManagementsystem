/* @odoo-module */

	import { AccountPaymentField } from "@account/components/account_payment_field/account_payment_field";
	import { patch } from "@web/core/utils/patch";
	import { Dialog } from "@web/core/dialog/dialog";
    import { registry } from "@web/core/registry";
    import { useService } from "@web/core/utils/hooks";

	patch(AccountPaymentField.prototype, {
		async assignOutstandingCredit(move_id,id) {

			let data = await this.orm.call(
               'account.move',
               'get_view_id',
               [[move_id],"bi_partial_payment_invoice.action_payment_wizard_open"],
            );
            var data_context = JSON.parse(data.context);
            data_context['move_id'] = move_id;
            data_context['line_id'] = id;

            data.context = JSON.stringify(data_context)

			this.action.doAction(data);
		}
	});













