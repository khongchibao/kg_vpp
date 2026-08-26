import frappe
from frappe.model.document import Document


def _cap_nhat_ton_kho(vat_tu: str, delta: int) -> None:
	# UPDATE nguyên tử: tránh race condition so với đọc-rồi-ghi (get_value + set_value).
	frappe.db.sql(
		"""
		UPDATE `tabVat Tu VPP`
		SET ton_kho_hien_tai = ton_kho_hien_tai + %s
		WHERE name = %s
		""",
		(delta, vat_tu),
	)


class PhieuNhapKhoVPP(Document):
	def on_submit(self):
		for row in self.chi_tiet_nhap:
			_cap_nhat_ton_kho(row.vat_tu, row.so_luong_nhap)

	def on_cancel(self):
		for row in self.chi_tiet_nhap:
			_cap_nhat_ton_kho(row.vat_tu, -row.so_luong_nhap)
