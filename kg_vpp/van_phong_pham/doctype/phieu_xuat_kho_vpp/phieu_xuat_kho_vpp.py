import frappe
from collections import defaultdict
from frappe.model.document import Document


class PhieuXuatKhoVPP(Document):
	def validate(self):
		for row in self.chi_tiet_xuat:
			trang_thai = frappe.db.get_value(
				"Phieu De Nghi Cap VPP", row.phieu_de_nghi, "workflow_state"
			)
			if trang_thai != "Đã tiếp nhận":
				frappe.throw(
					f"Phiếu đề nghị {row.phieu_de_nghi} chưa ở trạng thái "
					f'"Đã tiếp nhận" (hiện tại: {trang_thai}), không thể xuất kho.'
				)

		tong_theo_vat_tu = defaultdict(int)
		for row in self.chi_tiet_xuat:
			tong_theo_vat_tu[row.vat_tu] += row.so_luong_xuat

		for vat_tu, tong_xuat in tong_theo_vat_tu.items():
			ten_vat_tu, ton_kho = frappe.db.get_value(
				"Vat Tu VPP", vat_tu, ["ten_vat_tu", "ton_kho_hien_tai"]
			)
			if tong_xuat > (ton_kho or 0):
				frappe.throw(
					f'Vật tư "{ten_vat_tu}" ({vat_tu}): đang xin xuất {tong_xuat} '
					f"nhưng tồn kho hiện tại chỉ còn {ton_kho or 0}."
				)

	def on_submit(self):
		for row in self.chi_tiet_xuat:
			current_stock = frappe.db.get_value("Vat Tu VPP", row.vat_tu, "ton_kho_hien_tai")
			# Dùng set_value thay vì frappe.get_doc(...).save(): ton_kho_hien_tai chỉ
			# là một counter đơn giản trên Vat Tu VPP, giống cách làm ở
			# Phieu Nhap Kho VPP.on_submit().
			frappe.db.set_value(
				"Vat Tu VPP",
				row.vat_tu,
				"ton_kho_hien_tai",
				(current_stock or 0) - row.so_luong_xuat,
			)
