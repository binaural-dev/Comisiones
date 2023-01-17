from inspect import signature
from locale import currency
from unicodedata import name
from odoo import models, fields, http, tools
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import xlsxwriter
from odoo.http import request, Response
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from io import BytesIO
import base64
import logging
import pandas
from collections import OrderedDict

_logger = logging.getLogger(__name__)


class WizardMaxcamComision(models.TransientModel):
    _name = 'wizard.municipality.retentions'

    retention_id = fields.Many2one(
        'account.municipality.retentions', string='Retencion', required=True)

    def imprimir_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/get_excel_municipality_retention?&retention_id=%s' % (self.retention_id.id),
            'target': 'self'
        }

    def _excel_file(self, tabla, nombre, retention_id):
        company = self.env.company
        currency_symbol = self.env.ref('base.VEF').symbol
        retention = self.env['account.municipality.retentions'].browse(
            retention_id)
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
        boldWithBorder = workbook.add_format({'bold': 1, 'border': 1})
        boldWithBorderJustify = workbook.add_format(
            {'bold': 1, 'border': 1, 'text_wrap': True, 'valign': 'top', 'align': 'justify'})
        datos = tabla
        worksheet2 = workbook.add_worksheet(nombre)
        worksheet2.set_column('A:Z', 20)
        if company.logo_hacienda:
            logo = tools.ImageProcess(company.logo_hacienda)
            logo = logo.resize(200, 200)
            logo = logo.image_base64()
            logo_hacienda = BytesIO(base64.b64decode(logo))
            _logger.warning(logo_hacienda)
            worksheet2.insert_image('A2', "image.png", {
                                    'image_data': logo_hacienda})

        worksheet2.write(
            'C2', "A fin de cumplir con el art. 136 de la Ordenanza de Impuestos a las Actividades Economicas, Comercios, Servicios", bold)
        worksheet2.write(
            'C3', "o de indole similar y el Decreto A-05-01-2016   Art. 8 Reglamento de Retenciones sobre Retenciones Actividades Econòmicas", bold)
        worksheet2.write(
            'C5', "COMPROBANTE DE RETENCION IMPUESTO ACTIVIDADES ECONOMICAS PALAVECINO", bold)
        worksheet2.write(
            'D7', "AGENTE DE RETENCIÓN", bold)
        worksheet2.write(
            'G7', "COMPROBANTE:", boldWithBorder)
        worksheet2.write(
            'G8', retention.name, boldWithBorder)
        worksheet2.write_rich_string(
            'A11', bold, 'RAZÓN SOCIAL :', str(company.name))
        worksheet2.write_rich_string(
            'A12', bold, 'NUMERO DE REGISTRO ÚNICO DE INFORMACIÓN FISCAL: ', str(company.partner_id.vat))
        worksheet2.write_rich_string(
            'E12', bold, 'NUMERO DE LICENCIA DE ACTIVIDADES ECONOMICAS: ', str(company.economic_activity_number))
        worksheet2.write_rich_string(
            'A13', bold, 'DIRECCIÓN FISCAL: ', company.street)
        worksheet2.write(
            'G14', 'FECHA DE EMISIÓN O TRANSACCION', boldWithBorderJustify)
        worksheet2.write(
            'G15', retention.date_accounting.strftime("%d-%m-%Y"), boldWithBorderJustify)
        worksheet2.write(
            'H14', 'FECHA DE ENTREGA', boldWithBorderJustify)
        today = date.today()
        worksheet2.write(
            'H15', today.strftime("%d-%m-%Y"), boldWithBorderJustify)
        worksheet2.write(
            'D15', "CONTRIBUYENTE", bold)
        worksheet2.write_rich_string(
            'A16', bold, 'RAZÓN SOCIAL: ', str(retention.partner_id.name))
        worksheet2.write_rich_string(
            'A17', bold, 'NUMERO DE REGISTRO ÚNICO DE INFORMACIÓN FISCAL: ', str(retention.partner_id.prefix_vat) + str(retention.partner_id.vat))
        worksheet2.write(
            'G17', "Periodo Fiscal", boldWithBorder)
        worksheet2.write(
            'G18', "Año:", boldWithBorder)
        month = retention.date_accounting.month
        year = retention.date_accounting.year
        worksheet2.write(
            'G19', year, boldWithBorder)
        worksheet2.write(
            'H18', "Mes:", boldWithBorder)
        worksheet2.write(
            'H19',  month, boldWithBorder)
        worksheet2.write_rich_string(
            'A18', bold, 'DIRECCIÓN FISCAL: ', str(retention.partner_id.street))
        worksheet2.write(
            'D22', 'DATOS DE LA TRANSACCIÓN', bold)
        worksheet2.set_row(24, 23, merge_format)
        worksheet2.set_row(24, 23, merge_format)
        columnas = list(datos.columns.values)
        columns2 = [{'header': r} for r in columnas]
        money_format = workbook.add_format(
            {'num_format': '#,##0.00 "'+currency_symbol+'"'})
        control_format = workbook.add_format({'align': 'center'})
        porcent_format = workbook.add_format({'num_format': '0.0 %'})
        columns2[0].update({'format': control_format})
        columns2[5].update({'format': porcent_format})
        columns2[4].update({'format': money_format})
        columns2[7].update({'format': money_format})
        columns2[8].update({'format': money_format})

        data = datos.values.tolist()
        col3 = len(columns2)-1
        col2 = len(data)+25
        total_retained = 0
        for col in data:
            total_retained = col[8] + total_retained
        cells = xlsxwriter.utility.xl_range(24, 0, col2, col3)
        worksheet2.hide_gridlines(2)
        worksheet2.add_table(
            cells, {'data': data, 'total_row': True, 'columns': columns2, 'autofilter': False})
        worksheet2.write(
            'I'+str(col2+1), total_retained, money_format)
        boldWithBorderTop = workbook.add_format({'bold': 1, 'top': 1})

        worksheet2.write(
            'B'+str(col2+8), 'Firma del Beneficiario', boldWithBorderTop)

        worksheet2.write(
            'F'+str(col2+8), 'Firma del Beneficiario', boldWithBorderTop)

        signature = self.env['signature.config'].search(
            [('active', '=', True)], limit=1, order='id asc')

        if any(signature) and signature.signature:
            logo = tools.ImageProcess(signature.signature)
            logo = logo.resize(200, 200)
            logo = logo.image_base64()
            image_signature = BytesIO(base64.b64decode(logo))
            _logger.warning(image_signature)
            worksheet2.insert_image('F'+str(col2+4), "image.png", {
                                    'image_data': image_signature})

        workbook.close()
        data2 = data2.getvalue()
        return data2

    def _get_excel_municipality_retention(self, retention_id):

        retention = self.env['account.municipality.retentions'].browse(
            retention_id)

        lista = []
        cols = OrderedDict([
            ('Nº de la Op', ''),
            ('Fecha de Factura', ''),
            ('Nº de Factura', ''),
            ('Nº de Control', ''),
            ('Base Imponible', 0.00),
            ('Alícuota %', 0.00),
            ('Actividad Económica', 0.00),
            ('Impuesto Municipal Retenido', 0.00),
            ('IMPUESTO RETENIDO', 0.00),
        ])

        for index, retention_line in enumerate(retention.retention_line_ids):
            currency = self.env.company.currency_id.name
            baseImponible = 0
            impuestoMunicipal = 0

            if currency == 'USD':
                baseImponible = retention_line.invoice_id.foreign_amount_untaxed
                impuestoMunicipal = retention_line.foreign_total_retained
            else:
                baseImponible = retention_line.invoice_id.amount_untaxed
                impuestoMunicipal = retention_line.total_retained

            rows = OrderedDict()
            rows.update(cols)
            rows['Nº de la Op'] = index + 1
            rows['Fecha de Factura'] = retention_line.invoice_id.invoice_date.strftime(
                "%d-%m-%Y")
            rows['Nº de Factura'] = retention_line.invoice_id.name
            rows['Nº de Control'] = retention_line.invoice_id.correlative
            rows['Base Imponible'] = baseImponible
            rows['Alícuota %'] = retention_line.activity_aliquot/100
            rows['Actividad Económica'] = retention_line.economic_activity_id.name
            rows['Impuesto Municipal Retenido'] = impuestoMunicipal
            rows['IMPUESTO RETENIDO'] = impuestoMunicipal

            lista.append(rows)

        tabla = pandas.DataFrame(lista)
        return tabla.fillna(0)


class ControllerMunicipalityRetentionXlsx(http.Controller):

    @ http.route('/web/get_excel_municipality_retention', type='http', auth="user")
    @ serialize_exception
    def download_document(self, retention_id):
        filecontent = ''
        report_obj = request.env['wizard.municipality.retentions']

        if not retention_id:
            return request.not_found()

        tabla = report_obj._get_excel_municipality_retention(int(retention_id))
        retention = request.env['account.municipality.retentions'].browse(
            int(retention_id))
        name_document = ''

        if retention.state == 'draft':
            name_document = f"Ret Municipal Borrador {retention.date.strftime('%d-%m-%Y')}"
        elif retention.state == 'emitted':
            name_document = f"Ret Municipal {retention.name} {retention.date.strftime('%d-%m-%Y')}"
        else:
            name_document = "Ret Municipal Cancelada"

        filecontent = report_obj._excel_file(
            tabla, name_document, int(retention_id))

        if not filecontent:
            return Response("No hay datos para mostrar", content_type='text/html;charset=utf-8', status=500)
        return request.make_response(filecontent,
                                     [('Content-Type', 'application/pdf'), ('Content-Length', len(filecontent)),
                                      ('Content-Disposition', content_disposition(name_document+'.xlsx'))])
