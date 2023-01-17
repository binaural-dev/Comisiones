# from odoo import models, fields, api, _
# from odoo.tools.misc import formatLang

# class AccountCoaReportBinaural(models.AbstractModel):
#     _inherit = "account.coa.report"


#     @api.model
#     def _get_columns(self, options):
#         header1 = [
#             {'name': '', 'style': 'width:40%'},
#             {'name': _('Initial Balance'), 'class': 'number', 'colspan': 2},
#         ] + [
#             {'name': period['string'], 'class': 'number', 'colspan': 2}
#             for period in reversed(options['comparison'].get('periods', []))
#         ] + [
#             {'name': options['date']['string'], 'class': 'number', 'colspan': 2},
#             {'name': _('Total'), 'class': 'number', 'colspan': 2},
#         ]
#         header2 = [
#             {'name': '', 'style': 'width:40%'},
#             {'name': _(''), 'class': 'number o_account_coa_column_contrast'},
#             {'name': _(''), 'class': 'number o_account_coa_column_contrast'},
#         ]
#         if options.get('comparison') and options['comparison'].get('periods'):
#             header2 += [
#                 {'name': _(''), 'class': 'number o_account_coa_column_contrast'},
#                 {'name': _(''), 'class': 'number o_account_coa_column_contrast'},
#             ] * len(options['comparison']['periods'])
#         header2 += [
#             {'name': _(''), 'class': 'number o_account_coa_column_contrast'},
#             {'name': _(''), 'class': 'number o_account_coa_column_contrast'},
#             {'name': _(''), 'class': 'number o_account_coa_column_contrast'},
#             {'name': _(''), 'class': 'number o_account_coa_column_contrast'},
#         ]
#         return [header1, header2]

#     @api.model
#     def _get_lines(self, options, line_id=None):
#         # Create new options with 'unfold_all' to compute the initial balances.
#         # Then, the '_do_query' will compute all sums/unaffected earnings/initial balances for all comparisons.
#         new_options = options.copy()
#         new_options['unfold_all'] = True
#         options_list = self._get_options_periods_list(new_options)
#         accounts_results, taxes_results = self.env['account.general.ledger']._do_query(options_list, fetch_lines=False)

#         lines = []
#         totals = [0.0] * (2 * (len(options_list) + 2))

#         # Add lines, one per account.account record.
#         for account, periods_results in accounts_results:
#             sums = []
#             account_balance = 0.0
#             for i, period_values in enumerate(reversed(periods_results)):
#                 account_sum = period_values.get('sum', {})
#                 account_un_earn = period_values.get('unaffected_earnings', {})
#                 account_init_bal = period_values.get('initial_balance', {})

#                 if i == 0:
#                     # Append the initial balances.
#                     if account_init_bal.get('balance', 0.0) != None:
#                         balance_bal = account_init_bal.get('balance', 0.0)
#                     else:
#                         balance_bal = 0.0
#                     if account_un_earn.get('balance', 0.0) != None:
#                         balance_earn = account_un_earn.get('balance', 0.0)
#                     else:
#                         balance_earn = 0.0
#                     initial_balance = balance_bal + balance_earn
#                     sums += [
#                         initial_balance > 0 and initial_balance or 0.0,
#                         initial_balance < 0 and -initial_balance or 0.0,
#                     ]
#                     account_balance += initial_balance

#                 # Append the debit/credit columns.
#                 if account_sum.get('debit', 0.0) != None:
#                     debit_sum = account_sum.get('debit', 0.0)
#                 else:
#                     debit_sum = 0.0

#                 if account_sum.get('credit', 0.0) != None:
#                     credit_sum = account_sum.get('credit', 0.0)
#                 else:
#                     credit_sum = 0.0

#                 if account_init_bal.get('debit', 0.0) != None:
#                     debit_bal = account_init_bal.get('debit', 0.0)
#                 else:
#                     debit_bal = 0.0

#                 if account_init_bal.get('credit', 0.0) != None:
#                     credit_bal = account_init_bal.get('credit', 0.0)
#                 else:
#                     credit_bal = 0.0

#                 sums += [
#                     debit_sum - debit_bal,
#                     credit_sum - credit_bal,
#                 ]
#                 account_balance += sums[-2] - sums[-1]

#             # Append the totals.
#             sums += [
#                 account_balance > 0 and account_balance or 0.0,
#                 account_balance < 0 and -account_balance or 0.0,
#             ]
#             sums = [value * -1 if i % 2 == 0 else value for i, value in enumerate(sums)]
#             # account.account report line.
#             columns = []
#             for i, value in enumerate(sums):
#                 # Update totals.
#                 totals[i] += value

#                 # Create columns.
#                 columns.append(
#                     {'name': self.format_value(value, blank_if_zero=True), 'class': 'number', 'no_format_name': value})

#             name = account.name_get()[0][1]

#             lines.append({
#                 'id': account.id,
#                 'name': name,
#                 'title_hover': name,
#                 'columns': columns,
#                 'unfoldable': False,
#                 'caret_options': 'account.account',
#                 'class': 'o_account_searchable_line o_account_coa_column_contrast',
#             })

#         new_totals = []
#         i = 0
#         while i < len(totals):
#             new_totals.append('')
#             new_totals.append(totals[i] + totals[i+1])
#             i += 2


#         # Total report line.
#         lines.append({
#             'id': 'grouped_accounts_total',
#             'name': _('Total'),
#             'class': 'total o_account_coa_column_contrast',
#             'columns': [{'name': self.format_value(total), 'class': 'number'} for total in new_totals],
#             'level': 1,
#         })

#         return lines

#     @api.model
#     def format_value(self, amount, currency=False, blank_if_zero=False):
#         ''' Format amount to have a monetary display (with a currency symbol).
#         E.g: 1000 => 1000.0 $

#         :param amount:          A number.
#         :param currency:        An optional res.currency record.
#         :param blank_if_zero:   An optional flag forcing the string to be empty if amount is zero.
#         :return:                The formatted amount as a string.

#         MODIFICACIONES BINAURAL:
#             Se agregó una condición para que se muestre el símbolo de la moneda correspondiente en
#             cada reporte indistintamente de la moneda base (USD o BSF).
#         '''
#         if amount == '':
#             return amount
#         if self._name == "account.financial.html.report":
#             usd_report = True if (self._context.get("USD") or self.usd) else False
#         else:
#             usd_report = True if self._context.get("USD") else False

        
#         foreign_currency_id = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
#         foreign_currency_id = self.env["res.currency"].search([("id", '=', foreign_currency_id)])

#         if foreign_currency_id.id == 2:
#             currency_id = foreign_currency_id if usd_report else self.env.company.currency_id
#         else:
#             currency_id = self.env.company.currency_id if usd_report else foreign_currency_id

#         if currency_id.is_zero(amount):
#             if blank_if_zero:
#                 return ''
#             # don't print -0.0 in reports
#             amount = abs(amount)

#         if self.env.context.get('no_format'):
#             return amount
#         return formatLang(self.env, amount, currency_obj=currency_id)
