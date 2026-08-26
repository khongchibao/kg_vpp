frappe.ui.form.on("Phieu Tong Hop Mua VPP", {
	nap_du_lieu(frm) {
		if (!frm.doc.tu_ngay || !frm.doc.den_ngay) {
			frappe.msgprint(__("Vui lòng nhập Từ ngày và Đến ngày trước khi nạp dữ liệu."));
			return;
		}

		frappe.call({
			method: "kg_vpp.api.nap_du_lieu_tong_hop",
			args: {
				ten_phieu: frm.doc.name,
				tu_ngay: frm.doc.tu_ngay,
				den_ngay: frm.doc.den_ngay,
			},
			freeze: true,
			freeze_message: __("Đang nạp dữ liệu..."),
			callback(r) {
				if (!r.message) {
					return;
				}

				frm.clear_table("chi_tiet_tong_hop");
				r.message.forEach((row) => {
					const child = frm.add_child("chi_tiet_tong_hop");
					child.vat_tu = row.vat_tu;
					child.tong_so_luong_de_nghi = row.tong_so_luong_de_nghi;
					child.ton_kho_hien_tai = row.ton_kho_hien_tai;
				});
				frm.refresh_field("chi_tiet_tong_hop");
			},
		});
	},
});
