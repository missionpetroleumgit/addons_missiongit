import time
from openerp import models, fields, api, tools


class hr_payslip(models.Model):
	_inherit = 'hr.payslip'

	@api.multi
	def _compute_loans(self):
		array = []
		loan_ids = self.env['hr.loan.line'].search([('employee_id','=',self.employee_id.id),('loan_id.state','=','approve'), ('paid_date','>=',self.date_from),
												('paid_date','<',self.date_to)])
		for loan in loan_ids:
			array.append(loan.id)
		self.loan_ids = array

	@api.one
	def compute_total_paid_loan(self):
		total = 0.00
		for line in self.loan_ids:
			if line.paid == False:
				total += line.paid_amount
		self.total_amount_paid = total

# 	loan_ids = fields.One2many('hr.loan.line', 'payroll_id', string="Loans")
	loan_ids = fields.One2many('hr.loan.line','payroll_id',string="Loans", compute='_compute_loans')
	total_amount_paid = fields.Float(string="Total Loan Amount", compute= 'compute_total_paid_loan')

#	@api.multi
# 	def get_loan(self):
# 		array = []
# 		loan_ids = self.env['hr.loan.line'].search([('employee_id','=',self.employee_id.id),('paid','=',False)])
# 		for loan in loan_ids:
# 			array.append(loan.id)
# 		self.loan_ids = array
# 		return array

	@api.model
	def hr_verify_sheet(self):
		self.compute_sheet()
		array = []
		for line in self.loan_ids:
			if not line.paid:
				#array.append(line.id)
				line.action_paid_amount()
			else:
				line.payroll_id = False
		#self.loan_ids = array
		return self.write({'state': 'verify'})
	

