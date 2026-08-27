# kg_vpp — Ứng dụng quản lý Văn Phòng Phẩm (VPP)

Ứng dụng Frappe v16 duy nhất, module `Van Phong Pham`, site `dev.localhost`.
Ứng dụng quản lý đề nghị cấp, nhập kho, xuất kho, và tổng hợp mua văn phòng phẩm.

## 1. DocType

Ứng dụng có 6 DocType chính và 4 Child Table.

### DocType chính

| DocType | Vai trò |
|---|---|
| `Bo Phan VPP` | Danh mục bộ phận trong công ty. Thay thế cho `Department` của ERPNext/HRMS. |
| `Vat Tu VPP` | Danh mục vật tư. Có trường `ton_kho_hien_tai` (tồn kho hiện tại, chỉ đọc) và `dinh_muc_toi_thieu`. |
| `Phieu De Nghi Cap VPP` | Phiếu đề nghị cấp vật tư. Có child table `Chi Tiet De Nghi VPP`. Đi qua Workflow 4 trạng thái (xem mục 3). |
| `Phieu Nhap Kho VPP` | Phiếu nhập kho. Có child table `Chi Tiet Nhap Kho VPP`. Khi submit, cộng `ton_kho_hien_tai` của từng vật tư. Khi cancel, trừ lại. |
| `Phieu Xuat Kho VPP` | Phiếu xuất kho. Có child table `Chi Tiet Xuat Kho VPP`. Mỗi dòng xuất phải tham chiếu một `Phieu De Nghi Cap VPP` ở trạng thái "Đã tiếp nhận". Khi submit, trừ `ton_kho_hien_tai`. Khi cancel, cộng lại. |
| `Phieu Tong Hop Mua VPP` | Phiếu tổng hợp mua, gộp nhu cầu từ các phiếu đề nghị đã tiếp nhận trong một khoảng ngày. Có child table `Chi Tiet Tong Hop Mua VPP` và nút `Nạp dữ liệu` gọi API `kg_vpp.api.nap_du_lieu_tong_hop`. |

### Child Table

| Child Table | Thuộc DocType cha |
|---|---|
| `Chi Tiet De Nghi VPP` | `Phieu De Nghi Cap VPP` |
| `Chi Tiet Nhap Kho VPP` | `Phieu Nhap Kho VPP` |
| `Chi Tiet Xuat Kho VPP` | `Phieu Xuat Kho VPP` |
| `Chi Tiet Tong Hop Mua VPP` | `Phieu Tong Hop Mua VPP` |

Mỗi child table trên đều fetch `ten_vat_tu`, `qui_cach`, `dvt` từ `Vat Tu VPP` qua trường `vat_tu` (Link), để tránh nhập tay sai lệch với danh mục gốc.

## 2. Role

Ứng dụng dùng 3 Role tùy chỉnh, cộng với Role có sẵn `Employee` của Frappe core.

| Role | Vai trò trong quy trình |
|---|---|
| `Employee` | Nhân viên. Tạo và gửi phiếu đề nghị cấp VPP của chính mình. |
| `VPP Truong Bo Phan` | Trưởng bộ phận. Duyệt hoặc từ chối phiếu đề nghị của bộ phận mình. |
| `VPP Phong To Chuc` | Nhân viên phòng tổ chức. Tiếp nhận phiếu đã duyệt, thực hiện nhập kho và xuất kho, lập phiếu tổng hợp mua. |
| `VPP Truong Phong To Chuc` | Trưởng phòng tổ chức. Duyệt (submit) phiếu tổng hợp mua. |

Cả 3 Role tùy chỉnh và Workflow đều xuất ra fixture trong `kg_vpp/fixtures/`
(khai báo trong `hooks.py`, mục `fixtures`) để cài lại tự động qua `bench migrate`
trên site mới.

**Lưu ý về quyền submit:** một dòng permission có `submit: 1` nhưng `write: 0`
sẽ báo lỗi `PermissionError` khi thật sự submit, dù `bench migrate` không báo lỗi
gì. `Document._save()` luôn kiểm tra quyền `write` trước khi kiểm tra quyền
`submit`. Nếu cần Role chỉ được submit mà không được sửa, phải cấp `write: 1`
kèm `create: 0`, và luôn kiểm tra lại bằng một lệnh `doc.submit()` thật qua
`bench execute`, không chỉ đọc file JSON quyền.

## 3. Workflow

Workflow tên `Quy Trinh Phieu De Nghi Cap VPP`, gắn trên `Phieu De Nghi Cap VPP`,
trường trạng thái `workflow_state`. Workflow có 4 trạng thái theo thứ tự sau.

1. **Nháp** (docstatus 0) — `Employee` tạo và sửa phiếu.
2. **Chờ duyệt** (docstatus 0) — sau hành động "Gửi duyệt". `VPP Truong Bo Phan`
   duyệt (hành động "Duyệt", chuyển sang "Đã duyệt", đồng thời submit phiếu)
   hoặc từ chối (hành động "Từ chối", quay lại "Nháp").
3. **Đã duyệt** (docstatus 1) — `VPP Phong To Chuc` thực hiện hành động "Tiếp nhận".
4. **Đã tiếp nhận** (docstatus 1) — trạng thái cuối. Chỉ phiếu ở trạng thái này
   mới được phép xuất kho (kiểm tra trong `PhieuXuatKhoVPP.validate()`).

## 4. Quyết định kiến trúc: không phụ thuộc ERPNext/HRMS

Ứng dụng không cài ERPNext hay HRMS. Bench dev ban đầu chỉ có `frappe` và
`raven`, chưa có ERPNext.

Vì lý do đó, ứng dụng dùng:

- `Bo Phan VPP` (DocType tự viết) thay cho `Department` của ERPNext/HRMS.
- Trường Link `options: "User"` (ví dụ `nguoi_de_nghi`, `nguoi_nhap`, `nguoi_xuat`,
  `nguoi_lap`) thay cho Link tới `Employee` của HRMS.

Nếu sau này cài ERPNext/HRMS vào bench, cân nhắc kỹ trước khi đổi các Link này
sang `Department`/`Employee`, vì dữ liệu hiện tại và fixture Role/Workflow đều
xây trên giả định không có hai app đó.

## 5. Bài học về Workspace Sidebar / icon Desktop trên v16

Trên Frappe v16, `Workspace Sidebar` và mục icon Desktop không hiển thị ổn định
cho ứng dụng tùy chỉnh theo cách kỳ vọng. Cách khắc phục đã dùng: khai báo hook
`add_to_apps_screen` trong `hooks.py`, trỏ thẳng route `/app/van-phong-pham`.
Cách này đưa icon "Văn phòng phẩm" vào màn hình Apps (Default App switcher)
một cách ổn định, không phụ thuộc hành vi chưa ổn định của Workspace Sidebar.

Ứng dụng vẫn giữ file `Workspace Sidebar` (`kg_vpp/workspace_sidebar/van_phong_pham.json`)
và `Workspace` (`kg_vpp/van_phong_pham/workspace/van_phong_pham/van_phong_pham.json`)
cho điều hướng bên trong trang Workspace. Nhưng lối vào chính từ Desktop dựa
vào `add_to_apps_screen`, không dựa vào các file này.

## 6. Quy ước code

Business logic nằm trong file `.py` của controller DocType (ví dụ
`phieu_xuat_kho_vpp.py`, `phieu_nhap_kho_vpp.py`) hoặc trong `kg_vpp/api.py`
cho các API whitelist dùng chung. Ứng dụng không dùng Server Script cho logic
nghiệp vụ. Lý do: logic trong `.py` được review qua git, chạy test được, và
không sống ngoài tầm kiểm soát version control như Server Script trong DB.

Cập nhật số đếm tồn kho (`ton_kho_hien_tai`) dùng một câu lệnh SQL nguyên tử
(`frappe.db.sql` với `UPDATE ... SET x = x + %s`), không dùng
`frappe.db.get_value` rồi `frappe.db.set_value`. Đọc-rồi-ghi có thể mất một
lần cộng/trừ khi hai phiếu submit cùng lúc. Khi điều kiện cập nhật phải kiểm
tra tồn kho đủ (như xuất kho), thêm điều kiện vào `WHERE` và kiểm tra
`frappe.db._cursor.rowcount` để biết câu lệnh có thật sự chạy hay không.
Xem `phieu_xuat_kho_vpp.py`, hàm `_tru_ton_kho_neu_du`, để có ví dụ đầy đủ.

## 7. Người dùng test

4 tài khoản test đã tạo trên site `dev.localhost`, mỗi tài khoản ứng với một Role.

| Email | Role |
|---|---|
| `test.employee@vpp.local` | Employee |
| `test.truongbophan@vpp.local` | VPP Truong Bo Phan |
| `test.phongtochuc@vpp.local` | VPP Phong To Chuc |
| `test.truongphongtochuc@vpp.local` | VPP Truong Phong To Chuc |

Các tài khoản này chỉ tồn tại trong DB của `dev.localhost`, không nằm trong git.
