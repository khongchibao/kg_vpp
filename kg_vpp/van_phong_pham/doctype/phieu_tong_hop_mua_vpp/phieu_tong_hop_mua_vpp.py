import frappe
from frappe.model.document import Document


class PhieuTongHopMuaVPP(Document):
	def validate(self):
		if self.docstatus == 1 and not self.chi_tiet_tong_hop:
			frappe.throw("Chi tiết tổng hợp không được để trống khi trình phiếu.")
