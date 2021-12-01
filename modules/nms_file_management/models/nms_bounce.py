# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class InheritProductTemplateForm(models.Model):
    _inherit = 'product.template'

    h_type = fields.Selection(
        string='H Type',
        selection=[('H', 'H'), ('H3', 'H3'), ('H5', 'H5')] , tracking=True )
    # variant = fields.Char(string='Variant')


class InheritProductProductForm(models.Model):
    _inherit = 'product.product'

    h_type = fields.Selection(
        string='H Type',
        selection=[('H', 'H'), ('H3', 'H3'), ('H5', 'H5'), ] , tracking=True)
    # variant = fields.Char(string='Variant')


class nms_bounce_attachment_download(models.TransientModel):
    _name = 'nms.bounce.attachment.download'
    _description = 'nms.bounce.attachment.download'

    name = fields.Char(string='Name', default='nms bounce.txt')
    downloadable_attachment = fields.Binary(string='Attachment', readonly=True)


# *******  wizards for udf ASN multi reports******
class udf_asn_report_multi_wizard(models.TransientModel):
    _name = 'udf.asn.report.multi.wizard'
    _description = 'udf_asn_report_multi wizard'

    attachment_ids = fields.Many2many('udf.asn.report.multi', string='Attachments')


class udf_asn_report_multi(models.TransientModel):
    _name = 'udf.asn.report.multi'
    _description = 'udf_asn_report_multi'

    name = fields.Char(string='Name', default='Udf asn report.txt')
    downloadable_attachment = fields.Binary(string='Attachment', readonly=True)


# *******  wizards for udf ACTIVATION multi reports******
class activation_report_multi(models.TransientModel):
    _name = 'activation.report.multi'
    _description = 'udf_activation_report_multi wizard'

    attachment_ids = fields.Many2many('udf.activation.report.multi', string='Attachments')


class udf_activation_report_multi(models.TransientModel):
    _name = 'udf.activation.report.multi'
    _description = 'udf_activation_report_multi'

    name = fields.Char(string='Name', default='Udf Activation report.txt')
    downloadable_attachment = fields.Binary(string='Attachment', readonly=True)
