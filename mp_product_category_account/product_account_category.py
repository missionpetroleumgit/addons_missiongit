##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.onchange('categ_id')
    def update_product_accounts(self):
        for record in self:
            account_obj = self.env['account.account']
            importation_acc = account_obj.search([('code', '=', '101030109')])
            if self.categ_id:
                record.property_stock_account_input = record.categ_id.property_stock_account_input_categ
                record.property_account_expense = record.categ_id.property_stock_account_input_categ
                record.transit_account_id = importation_acc.id
                record.property_account_income = record.categ_id.property_account_income_categ
                record.property_account_cost_id = record.categ_id.property_stock_account_output_categ
                record.stock_input_account_id = record.categ_id.property_stock_account_input_categ
                record.stock_output_account_id = record.categ_id.property_stock_account_output_categ


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('categ_id')
    def update_product_accounts(self):
        account_obj = self.env['account.account']
        importation_acc = account_obj.search([('code', '=', '101030109')])
        for record in self:
            if self.categ_id:
                record.property_stock_account_input = record.categ_id.property_stock_account_input_categ
                record.property_account_expense = record.categ_id.property_stock_account_input_categ
                record.transit_account_id = importation_acc.id
                record.property_account_income = record.categ_id.property_account_income_categ
                record.property_account_cost_id = record.categ_id.property_stock_account_output_categ
                record.stock_input_account_id = record.categ_id.property_stock_account_input_categ
                record.stock_output_account_id = record.categ_id.property_stock_account_output_categ
