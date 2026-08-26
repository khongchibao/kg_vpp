import frappe
from frappe.model.document import Document


class PhieuNhapKhoVPP(Document):
	def on_submit(self):
		for row in self.chi_tiet_nhap:
			current_stock = frappe.db.get_value("Vat Tu VPP", row.vat_tu, "ton_kho_hien_tai")
			# Dùng set_value thay vì frappe.get_doc(...).save(): ton_kho_hien_tai chỉ
			# là một counter đơn giản trên Vat Tu VPP, không có validate()/lifecycle
			# logic nào cần chạy lại khi cập nhật nó, nên load cả Document + ghi version
			# log cho một phép cộng số lượng là dư thừa.
			frappe.db.set_value(
				"Vat Tu VPP",
				row.vat_tu,
				"ton_kho_hien_tai",
				(current_stock or 0) + row.so_luong_nhap,
			)
