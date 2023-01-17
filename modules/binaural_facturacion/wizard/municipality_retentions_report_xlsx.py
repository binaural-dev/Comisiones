from odoo import models, fields, http, tools
from datetime import date
import xlsxwriter
from odoo.http import request, Response
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from odoo.exceptions import MissingError
from io import BytesIO
import base64
import logging
import pandas
from collections import OrderedDict
from datetime import date
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class WizardMaxcamComision(models.TransientModel):
    _name = 'wizard.municipality.retentions.report'

    date_start = fields.Date(
        string='Fecha Inicio', required=True, default=date.today().replace(day=1))
    date_end = fields.Date(string='Fecha fin', required=True, default=date.today(
    ).replace(day=1)+relativedelta(months=1, days=-1))

    def imprimir_excel(self):
        retentions = self.env['account.municipality.retentions'].search(
            [('date_accounting', '>=', self.date_start), ('date_accounting', '<=', self.date_end), ('state', '=', 'emitted'), ('type', '=', "in_invoice")], order='date_accounting asc')

        if not any(retentions):
            raise MissingError(
                "Deben hacer Retenciones municipales emitidas en el rango de fechas, para emitir este reporte")
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/get_excel_municipality_retentions_report?id=%s' % self.id,
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
        company = self.env.company
        if company.logo_hacienda:
            logo = tools.ImageProcess(company.logo_hacienda)
            logo = logo.resize(200, 200)
            logo = logo.image_base64()
            logo_hacienda = BytesIO(base64.b64decode(logo))
            worksheet2.insert_image('A1', "image.png", {
                                    'image_data': logo_hacienda})
        worksheet2.write(
            'C2', "RENDICIÓN INFORMATIVA MENSUAL DEL AGENTE DE RETENCIÓN", bold)
        worksheet2.write(
            'D4', "ALCALDÍA DE PALAVECINO", bold)
        worksheet2.write(
            'A8', "AGENTE DE RETENCIÓN:", bold)
        worksheet2.write(
            'C8', company.name)
        worksheet2.write(
            'A9', "NUMERO DE REGISTRO UNICO DE INFORMACION FISCAL:", bold)
        worksheet2.write(
            'D9', str(company.partner_id.vat))
        worksheet2.write(
            'A10', "DIRECCION FISCAL:", bold)
        worksheet2.write(
            'B10', company.street)
        date = current_date_format(self.date_start)
        worksheet2.write(
            'A11', "MES Y AÑO DECLARADO:", bold)
        worksheet2.write(
            'C11', date)
        worksheet2.write(
            'A12', "FACTURA, ORDEN DE PAGO U OTRO INSTRUMENTO CONTABLE DONDE SE VERIFIQUE EL PAGO O ABONO EN CUENTA", bold)

        worksheet2.set_row(13, 23, merge_format)
        worksheet2.set_row(13, 23, merge_format)
        columnas = list(datos.columns.values)
        columns2 = [{'header': r} for r in columnas]
        currency_symbol = self.env.ref('base.VEF').symbol
        money_format = workbook.add_format(
            {'num_format': '#,##0.00 "'+currency_symbol+'"'})
        # control_format = workbook.add_format({'align': 'center'})
        porcent_format = workbook.add_format({'num_format': '0.0 %'})
        _logger.warning(len(columns2))
        _logger.warning(columns2)
        # columns2[0].update({'format': control_format})
        columns2[10].update({'format': porcent_format})
        # columns2[4].update({'format': money_format})
        columns2[9].update({'format': money_format})
        columns2[11].update({'format': money_format})

        data = datos.values.tolist()
        col3 = len(columns2)-1
        col2 = len(data)+14
        cells = xlsxwriter.utility.xl_range(13, 0, col2, col3)

        total_retained = 0
        for col in data:
            total_retained = col[11] + total_retained

        total = 0
        for col in data:
            total = col[9] + total
        worksheet2.hide_gridlines(2)
        worksheet2.add_table(
            cells, {'data': data, 'total_row': True, 'columns': columns2, 'autofilter': False})
        worksheet2.write(
            'L'+str(col2+1), total_retained, money_format)
        worksheet2.write(
            'J'+str(col2+1), total, money_format)
        worksheet2.write(
            'A'+str(col2+4), "Declaro, bajo juramento la veracidad de los datos contenidos en el presente formulario, quedando sometidos a las sanciones establecidas por la ley en   caso que determiné la falsedad de algún dato suministrado.", bold)
        worksheet2.write(
            'A'+str(col2+5), "Agente de retención Responsable de la Declaración ____________________________________", bold)
        worksheet2.write(
            'A'+str(col2+6), "Cédula de Identidad ___________________________________", bold)
        worksheet2.write(
            'A'+str(col2+7), "Cargo: ______________________________________________", bold)
        worksheet2.write('F'+str(col2+9), "Firma y sello", bold)
        workbook.close()
        data2 = data2.getvalue()
        return data2

    def _get_excel_municipality_retention_report(self):

        retentions = self.env['account.municipality.retentions'].search(
            [('date_accounting', '>=', self.date_start), ('date_accounting', '<=', self.date_end), ('state', '=', 'emitted'), ('type', '=', "in_invoice")], order='date_accounting asc')

        lista = []
        cols = OrderedDict([
            ('Nº', ''),
            ('Tipo de Instrumento', ''),
            ('Nº de Instrumento', ''),
            ('Fecha de Emision', ''),
            ('Contribuyente', ''),
            ('R.I.F.', ''),
            ('Domicilio Fiscal', ''),
            ('Descripcion del Documento', ''),
            ('Actividad Económica', ''),
            ('Monto Bruto', 0.00),
            ('Alícuota %', ''),
            ('Monto Retenido', 0.00),
        ])
        currency = self.env.company.currency_id.name
        numero = 1
        for retention in retentions:
            for retention_line in retention.retention_line_ids:

                baseImponible = 0
                impuestoMunicipal = 0

                if currency == 'USD':
                    baseImponible = retention_line.invoice_id.foreign_amount_untaxed
                    impuestoMunicipal = retention_line.foreign_total_retained
                else:
                    baseImponible = retention_line.invoice_id.amount_untaxed
                    impuestoMunicipal = retention_line.total_retained

                instrumento = ''

                if retention_line.invoice_id.move_type == ['in_invoice', 'out_invoice']:
                    instrumento = 'F'
                elif retention_line.invoice_id.move_type == ['in_refund', 'out_refund']:
                    instrumento = 'NC'

                rows = OrderedDict()
                rows.update(cols)
                rows['Nº'] = numero
                rows['Tipo de Instrumento'] = instrumento
                rows['Monto Bruto'] = baseImponible
                rows['Nº de Instrumento'] = retention.name
                rows['Fecha de Emision'] = retention.date_accounting.strftime(
                    '%d-%m-%Y')
                rows['Contribuyente'] = retention.partner_id.name
                rows['R.I.F.'] = str(
                    retention.partner_id.prefix_vat)+str(retention.partner_id.vat)
                rows['Domicilio Fiscal'] = retention.partner_id.street
                rows['Descripcion del Documento'] = retention_line.invoice_id.name
                rows['Actividad Económica'] = retention_line.economic_activity_id.name
                rows['Monto Bruto'] = baseImponible
                rows['Alícuota %'] = retention_line.activity_aliquot/100
                rows['Monto Retenido'] = impuestoMunicipal

                lista.append(rows)
                numero += 1
        tabla = pandas.DataFrame(lista)
        return tabla.fillna(0)


class ControllerMunicipalityRetentionXlsx(http.Controller):

    @ http.route('/web/get_excel_municipality_retentions_report', type='http', auth="user")
    @ serialize_exception
    def download_document(self, id):
        filecontent = ''
        if not id:
            return request.not_found()

        report_obj = request.env['wizard.municipality.retentions.report'].browse(
            int(id))

        tabla = report_obj._get_excel_municipality_retention_report()

        name_document = f"Reporte Retenciones Municipales {report_obj.date_start.strftime('%d-%m-%Y')} al {report_obj.date_end.strftime('%d-%m-%Y')}"

        filecontent = report_obj._excel_file(
            tabla, name_document)

        if not filecontent:
            return Response("No hay datos para mostrar", content_type='text/html;charset=utf-8', status=500)
        return request.make_response(filecontent,
                                     [('Content-Type', 'application/pdf'), ('Content-Length', len(filecontent)),
                                      ('Content-Disposition', content_disposition(name_document+'.xlsx'))])


def current_date_format(date):
    months = ("Enero", "Febrero", "Marzo", "Abri", "Mayo", "Junio", "Julio",
              "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre")
    month = months[date.month - 1]
    year = date.year
    message = "{} {}".format(month, year)
    return message
