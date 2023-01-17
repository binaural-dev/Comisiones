from odoo import models, fields, http, tools
from datetime import date
import xlsxwriter
from odoo.http import request, Response
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from io import BytesIO
import logging
import pandas
from collections import OrderedDict
from datetime import date
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class WizardMaxcamComision(models.TransientModel):
    _name = 'wizard.municipality.retentions.patent.report'

    date_start = fields.Date(
        string='Fecha Inicio', required=True, default=date.today().replace(day=1))
    date_end = fields.Date(string='Fecha fin', required=True, default=date.today(
    ).replace(day=1)+relativedelta(months=1, days=-1))

    def imprimir_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/get_excel_municipality_retentions_report_patent?id=%s' % self.id,
            'target': 'self'
        }

    def _excel_file(self, tabla, nombre):
        data2 = BytesIO()
        workbook = xlsxwriter.Workbook(data2, {'in_memory': True})
        merge_format = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'border': 1,
            'valign': 'vcenter',
            'fg_color': '#D3D3D3',
            'text_wrap': 1,
            'valign': 'top'
        })
        bold = workbook.add_format({'bold': 1})
        datos = tabla
        worksheet2 = workbook.add_worksheet(nombre)
        worksheet2.set_column('A:Z', 20)
        worksheet2.set_row(0, 23, merge_format)
        worksheet2.set_row(0, 23, merge_format)
        columnas = list(datos.columns.values)
        columns2 = [{'header': r} for r in columnas]
        currency_symbol = self.env.ref('base.VEF').symbol
        money_format = workbook.add_format(
            {'num_format': '#,##0.00 "'+currency_symbol+'"'})
        _logger.warning(columns2)
        columns2[3].update({'format': money_format})
        columns2[4].update({'format': money_format})
        columns2[5].update({'format': money_format})
        columns2[6].update({'format': money_format})
        columns2[7].update({'format': money_format})
        columns2[8].update({'format': money_format})
        columns2[9].update({'format': money_format})
        columns2[11].update({'format': money_format})
        columns2[13].update({'format': money_format})
        columns2[14].update({'format': money_format})
        columns2[15].update({'format': money_format})

        invoice_lines = self.env['account.move.line'].search(
            [('move_id.invoice_date', '>=', self.date_start), ('move_id.invoice_date', '<=', self.date_end), ('move_id.move_type', 'in', ["out_invoice", 'out_refund']), ('move_id.financial_document', '=', True)])

        invoice_lines = invoice_lines.filtered(
            lambda l: l.price_unit > 0)
        company_currency = self.env.company.currency_id.name

        nc_financial = 0
        nd_financial = 0

        for line in invoice_lines:
            if line.move_id.move_type == 'out_refund':
                if company_currency == 'USD':
                    nc_financial += line.foreign_price_unit
                else:
                    nc_financial += line.price_unit
            if line.move_id.move_type == 'out_invoice':
                if company_currency == 'USD':
                    nd_financial += line.foreign_price_unit
                else:
                    nd_financial += line.price_unit

        data = datos.values.tolist()
        col3 = len(columns2)-1
        col2 = len(data)+1
        cells = xlsxwriter.utility.xl_range(0, 0, col2, col3)

        worksheet2.hide_gridlines(2)
        worksheet2.add_table(
            cells, {'data': data, 'total_row': True, 'columns': columns2, 'autofilter': False})

        worksheet2.write('F'+str(col2+1), nc_financial, money_format)
        worksheet2.write('G'+str(col2+1), nd_financial, money_format)

        worksheet2.write_array_formula(
            'D'+str(col2+1), f'=SUM(D2:D{col2})', money_format)
        worksheet2.write_array_formula(
            'E'+str(col2+1), f'=SUM(E2:E{col2})', money_format)
        worksheet2.write_array_formula(
            'H'+str(col2+1), f'=SUM(H2:H{col2})', money_format)
        worksheet2.write_array_formula(
            'I'+str(col2+1), f'=SUM(I2:I{col2})', money_format)
        worksheet2.write_array_formula(
            'J'+str(col2+1), f'=SUM(J2:J{col2})', money_format)
        worksheet2.write_array_formula(
            'L'+str(col2+1), f'=SUM(L2:L{col2})', money_format)
        worksheet2.write_array_formula(
            'N'+str(col2+1), f'=SUM(N2:N{col2})', money_format)
        worksheet2.write_array_formula(
            'O'+str(col2+1), f'=SUM(O2:O{col2})', money_format)
        worksheet2.write_array_formula(
            'P'+str(col2+1), f'=SUM(P2:P{col2})', money_format)

        for line in range(2, col2+1):
            worksheet2.write_array_formula(
                f'C{line}', f"=D{line}/D{str(col2+1)}", money_format)
            worksheet2.write_array_formula(
                f'F{line}', f"=C{line}*F{str(col2+1)}", money_format)
            worksheet2.write_array_formula(
                f'H{line}', f"=D{line}-E{line}-F{line}+G{line}", money_format)
            worksheet2.write_array_formula(
                f'G{line}', f"=G{str(col2+1)}*C{line}", money_format)
            worksheet2.write_array_formula(
                f'I{line}', f"=H{line}*0.9", money_format)
            worksheet2.write_array_formula(
                f'J{line}', f"=H{line}-I{line}", money_format)
            worksheet2.write_array_formula(
                f'L{line}', f"=I{line}*K{line}/1000", money_format)
            worksheet2.write_array_formula(
                f'N{line}', f"=IF(L{line}>M{line};L{line};M{line})", money_format)
            worksheet2.write_array_formula(
                f'O{line}', f"=J{line}*K{line}/1000", money_format)
            worksheet2.write_formula(
                f'P{line}', f"=N{line}", money_format)

        workbook.close()
        data2 = data2.getvalue()
        return data2

    def _get_excel_municipality_retention_report(self):

        invoice_lines = self.env['account.move.line'].search(
            [('move_id.invoice_date', '>=', self.date_start), ('move_id.invoice_date', '<=', self.date_end), ('move_id.move_type', 'in', ["out_invoice", 'out_refund']), ('move_id.financial_document', '=', False)])

        invoice_lines = invoice_lines.filtered(
            lambda l: any(l.product_id.categ_id.ciu))

        groups = {}
        company_currency = self.env.company.currency_id.name

        for line in invoice_lines:
            price_unit = 0

            if company_currency == 'USD':
                price_unit = line.foreign_price_unit
            else:
                price_unit = line.price_unit
            if not line.product_id.categ_id.name in groups.keys():
                groups[line.product_id.categ_id.name] = {
                    "CIU": line.product_id.categ_id.ciu.name,
                    "sales_total": price_unit if line.move_id.move_type == 'out_invoice' else 0,
                    "refund_total": price_unit if line.move_id.move_type == 'out_refund' else 0,
                    "aliquot": line.product_id.categ_id.ciu.aliquot,
                    "minimum_monthly": line.product_id.categ_id.ciu.minimum_monthly,
                }
                continue

            groups[line.product_id.categ_id.name]["sales_total"] += price_unit if line.move_id.move_type == 'out_invoice' else 0
            groups[line.product_id.categ_id.name]["refund_total"] += price_unit if line.move_id.move_type == 'out_refund' else 0

        _logger.warning(groups)

        lista = []
        cols = OrderedDict([
            ('RUBROS', ''),
            ('CIU', ''),
            ('PRORRATA DEDUCCIONES', 0.0),
            ('VENTAS BRUTAS (Factura + ND)', 0.0),
            ('DEVOLUC. VENTAS (NC)', 0.0),
            ('DSTOS. VENTAS (NC Financiera)', 0.0),
            ('NOTAS DE DEBITO (ND financiera)', 0.0),
            ('INGRESOS 100%', 0.0),
            ('INGRESOS 90%', 0.0),
            ('INGRESOS 10%', 0.00),
            ('Alic %', ''),
            ('IMPUESTO', 0.00),
            ('MINIMO TRIBUTABLE', 0.00),
            ('ANTICIPO PERIODO', 0.00),
            ('IMPUESTO RESTANTE 10%', 0.00),
            ('ANTICIPO 90%', 0.00),
        ])

        numero = 1
        for line in groups.keys():
            rows = OrderedDict()
            rows.update(cols)
            rows['RUBROS'] = line
            rows['CIU'] = groups[line]['CIU']
            rows['VENTAS BRUTAS (Factura + ND)'] = groups[line]['sales_total']
            rows['DEVOLUC. VENTAS (NC)'] = groups[line]['refund_total']
            rows['Alic %'] = groups[line]['aliquot']
            rows['MINIMO TRIBUTABLE'] = groups[line]['minimum_monthly']

            lista.append(rows)
            numero += 1
        tabla = pandas.DataFrame(lista)
        return tabla.fillna(0)


class ControllerMunicipalityRetentionXlsx(http.Controller):

    @ http.route('/web/get_excel_municipality_retentions_report_patent', type='http', auth="user")
    @ serialize_exception
    def download_document(self, id):
        filecontent = ''
        if not id:
            return request.not_found()

        report_obj = request.env['wizard.municipality.retentions.patent.report'].browse(
            int(id))

        tabla = report_obj._get_excel_municipality_retention_report()

        name_document = f"Patente Impuesto Municipal {report_obj.date_start.strftime('%d-%m-%Y')} al {report_obj.date_end.strftime('%d-%m-%Y')}"

        filecontent = report_obj._excel_file(
            tabla, name_document)

        if not filecontent:
            return Response("No hay datos para mostrar", content_type='text/html;charset=utf-8', status=500)
        return request.make_response(filecontent,
                                     [('Content-Type', 'application/pdf'), ('Content-Length', len(filecontent)),
                                      ('Content-Disposition', content_disposition(name_document+'.xlsx'))])
