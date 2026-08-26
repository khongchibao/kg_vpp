import frappe
from frappe.model.document import Document


class PhieuDeNghiCapVPP(Document):
	def validate(self):
		if not self.chi_tiet_vat_tu:
			frappe.throw("Phải có ít nhất một dòng vật tư.")
