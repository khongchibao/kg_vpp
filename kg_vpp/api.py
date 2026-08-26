from collections import defaultdict

import frappe


@frappe.whitelist()
def nap_du_lieu_tong_hop(ten_phieu: str, tu_ngay: str, den_ngay: str):
	if ten_phieu and frappe.db.exists("Phieu Tong Hop Mua VPP", ten_phieu):
		frappe.has_permission("Phieu Tong Hop Mua VPP", "write", doc=ten_phieu, throw=True)
	else:
		frappe.has_permission("Phieu Tong Hop Mua VPP", "write", throw=True)

	ten_phieu_de_nghi = frappe.get_all(
		"Phieu De Nghi Cap VPP",
		filters={
			"workflow_state": "Đã tiếp nhận",
			"ngay_nhan_phieu": ["between", [tu_ngay, den_ngay]],
		},
		pluck="name",
	)

	tong_theo_vat_tu = defaultdict(int)
	if ten_phieu_de_nghi:
		# get_all bỏ qua permission CHỦ ĐÍCH: hàm này tổng hợp toàn công ty,
		# không giới hạn theo bộ phận của người dùng hiện tại.
		chi_tiet_vat_tu = frappe.get_all(
			"Chi Tiet De Nghi VPP",
			filters={
				"parenttype": "Phieu De Nghi Cap VPP",
				"parent": ["in", ten_phieu_de_nghi],
			},
			fields=["vat_tu", "so_luong"],
		)
		for row in chi_tiet_vat_tu:
			tong_theo_vat_tu[row.vat_tu] += row.so_luong

	ton_kho_theo_vat_tu = {}
	if tong_theo_vat_tu:
		ton_kho_theo_vat_tu = {
			row.name: row.ton_kho_hien_tai
			for row in frappe.get_all(
				"Vat Tu VPP",
				filters={"name": ["in", list(tong_theo_vat_tu.keys())]},
				fields=["name", "ton_kho_hien_tai"],
			)
		}

	ket_qua = []
	for vat_tu, tong_so_luong in tong_theo_vat_tu.items():
		ket_qua.append(
			{
				"vat_tu": vat_tu,
				"tong_so_luong_de_nghi": tong_so_luong,
				"ton_kho_hien_tai": ton_kho_theo_vat_tu.get(vat_tu) or 0,
			}
		)

	return ket_qua
