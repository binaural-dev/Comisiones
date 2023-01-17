import json
from odoo import models, api, _
from collections import OrderedDict
from odoo.tools.misc import formatLang


class AccountReportBinaural(models.AbstractModel):
    _inherit = 'account.report'

    @api.model
    def _get_options(self, previous_options=None):
        """
        Obtenemos las opciones de moneda,
        verificamos la opciones anteriores o agregamos las opciones si no existen
        """
        alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
        alternate_currency = self.env['res.currency'].browse(alternate_currency)
        handlers = OrderedDict({'currency': [
            {'name': alternate_currency.name, 'id': alternate_currency.id, 'selected': False},
            {'name': self.env.user.company_id.currency_id.name, 'id': self.env.user.currency_id.id, 'selected': True}]}
        )
        current_options = super(AccountReportBinaural, self)._get_options(previous_options)

        for key, handler in handlers.items():
            if previous_options:
                currency_previus = previous_options.get('currency', False)
            else:
                currency_previus = False

            if currency_previus:
                previous_handler_value = previous_options[key]
            else:
                previous_handler_value = handler
            current_options[key] = previous_handler_value
        return current_options

    @api.model
    def format_value(self, amount, currency=False, blank_if_zero=False):
        ''' Format amount to have a monetary display (with a currency symbol).
        E.g: 1000 => 1000.0 $

        :param amount:          A number.
        :param currency:        An optional res.currency record.
        :param blank_if_zero:   An optional flag forcing the string to be empty if amount is zero.
        :return:                The formatted amount as a string.

        MODIFICACIONES BINAURAL:
            Se agregó una condición para que se muestre el símbolo de la moneda correspondiente en
            cada reporte indistintamente de la moneda base (USD o BSF).
        '''

        if self._name == "account.financial.html.report":
            usd_report = True if (self._context.get("USD") or self.usd) else False
        else:
            usd_report = True if self._context.get("USD") else False

        
        foreign_currency_id = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
        foreign_currency_id = self.env["res.currency"].search([("id", '=', foreign_currency_id)])

        if foreign_currency_id.id == 2:
            currency_id = foreign_currency_id if usd_report else self.env.company.currency_id
        else:
            currency_id = self.env.company.currency_id if usd_report else foreign_currency_id

        if currency_id.is_zero(amount):
            if blank_if_zero:
                return ''
            # don't print -0.0 in reports
            amount = abs(amount)

        if self.env.context.get('no_format'):
            return amount
        return formatLang(self.env, amount, currency_obj=currency_id)

    def print_pdf(self, options):
        usd_report = True if self._context.get("USD") else False
        if usd_report:
            return {
                    'type': 'ir_actions_account_report_download',
                    'data': {'model': self.env.context.get('model'),
                            'options': json.dumps(options),
                            'output_format': 'pdf',
                            'USD': usd_report,
                            'financial_id': self.env.context.get('id'),
                            }
                    }
        else:
            return {
                    'type': 'ir_actions_account_report_download',
                    'data': {'model': self.env.context.get('model'),
                            'options': json.dumps(options),
                            'output_format': 'pdf',
                            'financial_id': self.env.context.get('id'),
                            }
                    }

    def print_xlsx(self, options):
        usd_report = True if self._context.get("USD") else False
        if usd_report:
            return {
                    'type': 'ir_actions_account_report_download',
                    'data': {'model': self.env.context.get('model'),
                             'options': json.dumps(options),
                             'output_format': 'xlsx',
                             'USD': usd_report,
                             'financial_id': self.env.context.get('id'),
                             }
                    }
        else:
            return {
                    'type': 'ir_actions_account_report_download',
                    'data': {'model': self.env.context.get('model'),
                             'options': json.dumps(options),
                             'output_format': 'xlsx',
                             'financial_id': self.env.context.get('id'),
                             }
                    }

    def print_xml(self, options):
        usd_report = True if self._context.get("USD") else False
        if usd_report:
            return {
                    'type': 'ir_actions_account_report_download',
                    'data': {'model': self.env.context.get('model'),
                             'options': json.dumps(options),
                             'output_format': 'xml',
                             'USD': usd_report,
                             'financial_id': self.env.context.get('id'),
                             }
                    }
        else:
            return {
                    'type': 'ir_actions_account_report_download',
                    'data': {'model': self.env.context.get('model'),
                             'options': json.dumps(options),
                             'output_format': 'xml',
                             'financial_id': self.env.context.get('id'),
                             }
                    }

    def print_txt(self, options):
        usd_report = True if self._context.get("USD") else False
        if usd_report:
            return {
                    'type': 'ir_actions_account_report_download',
                    'data': {'model': self.env.context.get('model'),
                             'options': json.dumps(options),
                             'output_format': 'txt',
                             'USD': usd_report,
                             'financial_id': self.env.context.get('id'),
                             }
                    }
        else:
            return {
                    'type': 'ir_actions_account_report_download',
                    'data': {'model': self.env.context.get('model'),
                             'options': json.dumps(options),
                             'output_format': 'txt',
                             'financial_id': self.env.context.get('id'),
                             }
                    }
