import frappe
from collections import defaultdict
from frappe.model.document import Document


def _tru_ton_kho_neu_du(vat_tu: str, so_luong: int) -> int:
	# UPDATE nguyên tử có điều kiện: chỉ trừ kho nếu tồn kho tại thời điểm ghi
	# vẫn còn đủ. Trả về số dòng bị ảnh hưởng để caller biết có trừ được không —
	# đây là chốt chặn cuối cùng, đáng tin cậy hơn validate() vì validate() và
	# on_submit() không nằm trong cùng một khoảnh khắc (có thể có phiếu khác chen vào).
	frappe.db.sql(
		"""
		UPDATE `tabVat Tu VPP`
		SET ton_kho_hien_tai = ton_kho_hien_tai - %s
		WHERE name = %s AND ton_kho_hien_tai >= %s
		""",
		(so_luong, vat_tu, so_luong),
	)
	return frappe.db._cursor.rowcount


def _cong_ton_kho(vat_tu: str, so_luong: int) -> None:
	frappe.db.sql(
		"""
		UPDATE `tabVat Tu VPP`
		SET ton_kho_hien_tai = ton_kho_hien_tai + %s
		WHERE name = %s
		""",
		(so_luong, vat_tu),
	)


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
			vat_tu_doc = frappe.db.get_value(
				"Vat Tu VPP", vat_tu, ["ten_vat_tu", "ton_kho_hien_tai"], as_dict=True
			)
			if vat_tu_doc is None:
				frappe.throw(f'Vật tư "{vat_tu}" không tồn tại.')
			if tong_xuat > (vat_tu_doc.ton_kho_hien_tai or 0):
				frappe.throw(
					f'Vật tư "{vat_tu_doc.ten_vat_tu}" ({vat_tu}): đang xin xuất {tong_xuat} '
					f"nhưng tồn kho hiện tại chỉ còn {vat_tu_doc.ton_kho_hien_tai or 0}."
				)

	def on_submit(self):
		for row in self.chi_tiet_xuat:
			if _tru_ton_kho_neu_du(row.vat_tu, row.so_luong_xuat) == 0:
				ten_vat_tu = frappe.db.get_value("Vat Tu VPP", row.vat_tu, "ten_vat_tu") or row.vat_tu
				frappe.throw(
					f'Vật tư "{ten_vat_tu}": tồn kho không đủ để xuất {row.so_luong_xuat} '
					f"(tồn kho có thể đã thay đổi kể từ lúc kiểm tra)."
				)

	def on_cancel(self):
		for row in self.chi_tiet_xuat:
			_cong_ton_kho(row.vat_tu, row.so_luong_xuat)
