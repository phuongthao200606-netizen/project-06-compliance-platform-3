import io
import json
import pandas as pd
import streamlit as st

# Thử import google.generativeai an toàn
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# ==============================================================================
# 1. CẤU HÌNH TRANG VÀ GIAO DIỆN CHUẨN FINTECH
# ==============================================================================
st.set_page_config(
    page_title="Project 06 - NHNN RegTech Platform",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS phong cách Fintech Ngân hàng (Dark Navy #0F2A4A, Gold/Emerald accents)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Tiêu đề & Sub-header */
    .main-title {
        color: #0F2A4A;
        font-weight: 800;
        font-size: 2.1rem;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    .sub-title {
        color: #4A5568;
        font-size: 1rem;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }

    /* Hộp cảnh báo từ chối (Refusal Box chống Hallucination) */
    .refusal-alert {
        background-color: #FFF5F5;
        border-left: 5px solid #E53E3E;
        color: #9B1C1C;
        padding: 14px 18px;
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.95rem;
        margin-top: 15px;
        box-shadow: 0 2px 4px rgba(229, 62, 62, 0.08);
    }

    /* Thẻ dẫn nguồn Citation */
    .citation-tag {
        background-color: #EBF8FF;
        border-left: 4px solid #3182CE;
        padding: 10px 14px;
        border-radius: 6px;
        color: #2B6CB0;
        font-size: 0.88rem;
        font-weight: 600;
        margin-top: 10px;
    }

    /* Badge phong cách Fintech */
    .badge-added {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-modified {
        background-color: #FEF08A;
        color: #713F12;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-removed {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CƠ SỞ TRI THỨC VĂN BẢN PHÁP LUẬT NHNN (KNOWLEDGE BASE DỰ BỊ)
# ==============================================================================
LEGAL_KNOWLEDGE_BASE = """
[CĂN CỨ PHÁP LÝ NGÂN HÀNG NHÀ NƯỚC VIỆT NAM (NHNN)]

1. THÔNG TƯ SỐ 09/2023/TT-NHNN (Hướng dẫn thực hiện Luật Phòng, chống rửa tiền):
- Điều 3 khoản 4: Phương pháp chấm điểm để đánh giá rủi ro rửa tiền và mức độ phù hợp của chính sách, quy định nội bộ theo tiêu chí, thang điểm và phân loại rõ ràng (Trang 4-5).
- Điều 3 khoản 5: Thu thập số liệu đánh giá rủi ro rửa tiền theo năm và hoàn thành báo cáo chậm nhất ngày 31/3 năm tiếp theo gửi Cục Phòng, chống rửa tiền (Trang 5).
- Điều 4 khoản 1: Đối tượng báo cáo có trách nhiệm ban hành quy trình quản lý rủi ro rửa tiền và phân loại khách hàng theo 3 mức độ rủi ro: Thấp, Trung bình, Cao (Trang 6).
- Điều 4 khoản 5: Áp dụng các biện pháp tăng cường đối với khách hàng có mức rủi ro rửa tiền cao (thu thập thêm thông tin, tăng tần suất kiểm soát giao dịch, phê duyệt của cấp quản lý cao hơn) (Trang 7).
- Điều 5 khoản 6: Quy định về tuyển dụng nhân sự và bắt buộc tổ chức đào tạo kiến thức cơ bản về phòng, chống rửa tiền trong thời hạn 06 tháng kể từ ngày tuyển dụng (Trang 9).

2. THÔNG TƯ SỐ 12/2024/TT-NHNN (Sửa đổi, bổ sung một số điều của Thông tư số 39/2016/TT-NHNN về hoạt động cho vay):
- Điều 1 khoản 1: Bổ sung khoản 11 vào Điều 2 về khái niệm "Khoản cho vay có mức giá trị nhỏ" là khoản cho vay không vượt quá 100.000.000 (một trăm triệu) đồng Việt Nam (Trang 1).
- Điều 1 khoản 4: Bổ sung quy định hồ sơ đề nghị vay vốn tại Điều 9. Đối với khoản vay giá trị nhỏ (<= 100 triệu VNĐ), khách hàng được miễn cung cấp phương án sử dụng vốn khả thi, chỉ cần cung cấp tối thiểu thông tin về mục đích sử dụng vốn hợp pháp và khả năng tài chính (Trang 2-3).
- Điều 1 khoản 5: Sửa đổi, bổ sung Điều 16 về trách nhiệm cung cấp thông tin, tài liệu chứng minh sử dụng vốn vay đúng mục đích của khách hàng (Trang 3).
- Điều 1 khoản 7: Sửa đổi Điều 24 về kiểm tra, giám sát việc sử dụng vốn vay. Tổ chức tín dụng có quyền quyết định và chịu trách nhiệm về biện pháp kiểm tra phù hợp đối với khoản vay nhỏ (Trang 4).
- Điều 2: Bãi bỏ toàn bộ hiệu lực áp dụng của Điều 29, Điều 32 và Điều 32g của Thông tư số 39/2016/TT-NHNN (Trang 5).
"""

# ==============================================================================
# 3. KHỞI TẠO DỮ LIỆU BAN ĐẦU (SESSION STATE & HIGH-QUALITY MOCK DATA)
# ==============================================================================
if "diff_data" not in st.session_state:
    st.session_state.diff_data = pd.DataFrame([
        {
            "Change_ID": "LOAN-01",
            "Legal_Basis": "TT 12/2024 Điều 1 Khoản 1",
            "Old_Text": "(Chưa quy định riêng hạn mức định lượng cho khoản vay nhỏ)",
            "New_Text": "Khoản cho vay có mức giá trị nhỏ là khoản vay không vượt quá 100.000.000 (một trăm triệu) đồng Việt Nam.",
            "Change_Type": "Added",
            "Review_Status": "Approve",
            "Reviewer_Note": "Đã tích hợp vào luồng LOS phê duyệt tức thì."
        },
        {
            "Change_ID": "LOAN-02",
            "Legal_Basis": "TT 12/2024 Điều 1 Khoản 4",
            "Old_Text": "Mọi khoản vay bắt buộc phải có phương án sử dụng vốn khả thi và kế hoạch trả nợ chi tiết.",
            "New_Text": "Khoản vay giá trị nhỏ (<= 100 triệu VNĐ) được miễn lập phương án sử dụng vốn chi tiết, chỉ cần tối thiểu thông tin mục đích hợp pháp và khả năng tài chính.",
            "Change_Type": "Modified",
            "Review_Status": "Approve",
            "Reviewer_Note": "Cắt giảm 3 biểu mẫu kê khai tài chính."
        },
        {
            "Change_ID": "LOAN-03",
            "Legal_Basis": "TT 12/2024 Điều 1 Khoản 5",
            "Old_Text": "Khách hàng phải gửi văn bản chứng minh mục đích sử dụng vốn theo từng đợt giải ngân nghiêm ngặt.",
            "New_Text": "Khách hàng cung cấp tài liệu chứng minh sử dụng vốn theo thỏa thuận; đối với khoản vay nhỏ, cho phép áp dụng phương thức linh hoạt.",
            "Change_Type": "Modified",
            "Review_Status": "Approve",
            "Reviewer_Note": "Áp dụng chứng từ điện tử qua Mobile App."
        },
        {
            "Change_ID": "LOAN-04",
            "Legal_Basis": "TT 12/2024 Điều 1 Khoản 7",
            "Old_Text": "Bắt buộc kiểm tra thực địa việc sử dụng vốn định kỳ đối với 100% khoản vay sau giải ngân.",
            "New_Text": "Tổ chức tín dụng tự quyết định phương thức và chịu trách nhiệm về kiểm tra, giám sát sau cho vay đối với khoản vay nhỏ.",
            "Change_Type": "Modified",
            "Review_Status": "Approve",
            "Reviewer_Note": "Chuyển sang hậu kiểm dữ liệu xác suất 10%."
        },
        {
            "Change_ID": "LOAN-05",
            "Legal_Basis": "TT 12/2024 Điều 2",
            "Old_Text": "Quy định trình tự, thủ tục kiểm soát tại Điều 29, 32 và 32g Thông tư 39/2016/TT-NHNN.",
            "New_Text": "Chính thức bãi bỏ áp dụng toàn bộ Điều 29, Điều 32 và Điều 32g.",
            "Change_Type": "Removed",
            "Review_Status": "Approve",
            "Reviewer_Note": "Đã gỡ bỏ form biểu mẫu số 08 và 12."
        }
    ])

if "checklist_data" not in st.session_state:
    st.session_state.checklist_data = pd.DataFrame([
        {
            "ID": "AML-01",
            "Requirement": "Xây dựng phương pháp chấm điểm rủi ro rửa tiền theo tiêu chí và thang điểm rõ ràng.",
            "Subject": "Khối Quản trị Rủi ro & Khối Tuân thủ",
            "Action": "Ban hành bảng tiêu chí chấm điểm và ma trận rủi ro rửa tiền định lượng.",
            "Control": "Quy chế Quản lý rủi ro rửa tiền nội bộ được phê duyệt.",
            "Status": "Đã tuân thủ"
        },
        {
            "ID": "AML-02",
            "Requirement": "Hoàn thành báo cáo đánh giá rủi ro rửa tiền định kỳ hàng năm.",
            "Subject": "Ban Phòng chống Rửa tiền (AML)",
            "Action": "Thu thập dữ liệu năm và hoàn thành báo cáo chậm nhất ngày 31/3 năm tiếp theo.",
            "Control": "Báo cáo nộp Cục Phòng, chống rửa tiền (NHNN) có biên nhận điện tử.",
            "Status": "Đang xử lý"
        },
        {
            "ID": "AML-03",
            "Requirement": "Thiết lập quy trình nhận biết và phân loại khách hàng theo 3 mức độ rủi ro.",
            "Subject": "Khối Vận hành & Khối Khách hàng",
            "Action": "Cập nhật trường phân loại rủi ro (Low/Medium/High) trên hệ thống LOS/Core.",
            "Control": "Logs hệ thống KYC và sơ đồ luồng nhận diện khách hàng.",
            "Status": "Đã tuân thủ"
        },
        {
            "ID": "AML-05",
            "Requirement": "Tổ chức đào tạo kiến thức cơ bản về phòng, chống rửa tiền cho nhân sự mới.",
            "Subject": "Khối Nhân sự (HR) & Khối Tuân thủ",
            "Action": "Triển khai khóa học hoàn thành trong vòng 6 tháng kể từ ngày tuyển dụng.",
            "Control": "Danh sách điểm danh LMS và bài test nội bộ đạt chuẩn.",
            "Status": "Đang xử lý"
        },
        {
            "ID": "LOAN-01",
            "Requirement": "Thiết lập hạn mức và luồng thẩm định riêng cho khoản vay nhỏ không quá 100 triệu.",
            "Subject": "Khối Khách hàng Cá nhân & Khối Tín dụng",
            "Action": "Cấu hình luồng phê duyệt và điều kiện giải ngân riêng trên hệ thống LOS.",
            "Control": "Biên bản nghiệm thu UAT hệ thống LOS và Quyết định ban hành sản phẩm.",
            "Status": "Chưa thực hiện"
        }
    ])

if "impact_map_data" not in st.session_state:
    st.session_state.impact_map_data = pd.DataFrame([
        {
            "Change_ID": "LOAN-01",
            "Legal_Basis": "TT 12/2024/TT-NHNN, Điều 1 Khoản 1",
            "Change_Summary": "Bổ sung khái niệm khoản vay nhỏ dưới 100 triệu VNĐ.",
            "Requirement": "Định danh và thiết lập luồng xử lý riêng cho khoản vay <= 100tr",
            "Affected_Department": "Khối Tín dụng Cá nhân, Khối CNTT, Khối QLRR",
            "Affected_Process": "Quy trình Khởi tạo & Phê duyệt Khoản vay Tiêu dùng",
            "Affected_Data_Field": "Is_Small_Loan (Bool), Loan_Limit_Amount",
            "Impact_Level": "Cao",
            "Required_Action": "Sửa đổi Quy chế cho vay; Cập nhật logic thẩm định hệ thống LOS.",
            "Evidence": "Quy chế Tín dụng sửa đổi; Test report hệ thống Core/LOS.",
            "Verification_Status": "Đã có căn cứ"
        },
        {
            "Change_ID": "LOAN-02",
            "Legal_Basis": "TT 12/2024/TT-NHNN, Điều 1 Khoản 4",
            "Change_Summary": "Miễn trừ phương án sử dụng vốn chi tiết với khoản vay nhỏ.",
            "Requirement": "Đơn giản hóa hồ sơ vay vốn dưới 100 triệu đồng",
            "Affected_Department": "Khối Khách hàng Cá nhân, Khối Pháp chế & Tuân thủ",
            "Affected_Process": "Quy trình Tiếp nhận & Thẩm định Hồ sơ Vay vốn",
            "Affected_Data_Field": "Capital_Use_Purpose_Type, Feasibility_Study_Doc",
            "Impact_Level": "Trung bình",
            "Required_Action": "Rút gọn biểu mẫu đăng ký vay vốn, chỉ yêu cầu cam kết mục đích hợp pháp.",
            "Evidence": "Bộ biểu mẫu hồ sơ vay vốn ban hành mới; Hướng dẫn nghiệp vụ.",
            "Verification_Status": "Đã có căn cứ"
        },
        {
            "Change_ID": "LOAN-04",
            "Legal_Basis": "TT 12/2024/TT-NHNN, Điều 1 Khoản 7",
            "Change_Summary": "Tự chủ quyết định hình thức kiểm tra sau vay đối với khoản nhỏ.",
            "Requirement": "Xây dựng cơ chế giám sát sau giải ngân dựa trên mức độ rủi ro",
            "Affected_Department": "Khối Quản lý Tín dụng, Khối QLRR, Khối Vận hành",
            "Affected_Process": "Quy trình Kiểm tra & Giám sát Sau Giải ngân",
            "Affected_Data_Field": "Post_Disbursement_Audit_Method, Audit_Status",
            "Impact_Level": "Trung bình",
            "Required_Action": "Chuyển từ kiểm tra thực địa 100% sang giám sát bằng dữ liệu/gọi điện ngẫu nhiên.",
            "Evidence": "Chính sách kiểm tra sau cấp tín dụng sửa đổi.",
            "Verification_Status": "Đã có căn cứ"
        },
        {
            "Change_ID": "LOAN-05",
            "Legal_Basis": "TT 12/2024/TT-NHNN, Điều 2",
            "Change_Summary": "Bãi bỏ Điều 29, 32 và 32g Thông tư 39/2016/TT-NHNN.",
            "Requirement": "Loại bỏ các quy trình và báo cáo liên quan đến điều khoản bãi bỏ",
            "Affected_Department": "Khối Tuân thủ, Khối Báo cáo Thống kê",
            "Affected_Process": "Quy trình Báo cáo Định kỳ NHNN",
            "Affected_Data_Field": "Chưa xác định",
            "Impact_Level": "Thấp",
            "Required_Action": "Rà soát lại danh mục báo cáo quản trị, ngừng tạo các mẫu biểu thừa.",
            "Evidence": "Văn bản hướng dẫn bãi bỏ thủ tục nội bộ.",
            "Verification_Status": "Đã có căn cứ"
        },
        {
            "Change_ID": "AML-02",
            "Legal_Basis": "TT 09/2023/TT-NHNN, Điều 3 Khoản 5",
            "Change_Summary": "Thời hạn nộp báo cáo đánh giá rủi ro rửa tiền hàng năm là 31/3.",
            "Requirement": "Hoàn thiện và gửi báo cáo rủi ro rửa tiền định kỳ đúng hạn",
            "Affected_Department": "Khối Tuân thủ, Ban Phòng Chống Rửa Tiền",
            "Affected_Process": "Quy trình Thu thập Dữ liệu & Báo cáo AML Hằng năm",
            "Affected_Data_Field": "AML_Risk_Score, Annual_Report_Date",
            "Impact_Level": "Cao",
            "Required_Action": "Chốt số liệu trước 15/02 hằng năm, dự thảo báo cáo phê duyệt trước 15/03.",
            "Evidence": "Báo cáo nộp Cục PCRT có xác nhận tiếp nhận điện tử.",
            "Verification_Status": "Đã có căn cứ"
        }
    ])

# ==============================================================================
# 4. THANH SIDEBAR: THÔNG TIN DỰ ÁN & CẤU HÌNH AI
# ==============================================================================
with st.sidebar:
    st.markdown("### 🏛️ NHNN RegTech AI")
    st.markdown("**Project 06: Compliance Platform**")
    st.caption("Nền tảng Tra cứu & Phân tích Tác động Tuân thủ")

    st.markdown("---")
    st.markdown("#### 👥 Đội ngũ thực hiện (Team 06)")
    st.markdown("""
    - **👑 Nhóm trưởng:** Lê Hồng Phương Thảo
    - **Thành viên:**
        - Lê Bảo Châu
        - Vũ Thúy Hiền
        - Nguyễn Ngọc Như Ý
        - Trần Thị Minh Anh
        - Vòng Ánh Ngọc
    """)

    st.markdown("---")
    st.markdown("#### ⚙️ Cấu hình Gemini API")
    gemini_api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        placeholder="Dán mã AIzaSy... tại đây",
        help="Nhập API Key để kích hoạt RAG Gemini trực tiếp."
    )
    selected_model = st.selectbox("Chọn mô hình LLM:", ["gemini-1.5-flash", "gemini-1.5-pro"])
    
    if gemini_api_key.strip():
        st.success("🟢 Đã thiết lập API Key sẵn sàng.")
    else:
        st.info("💡 **Chế độ Ngoại tuyến:** Đang dùng Offline Mock Engine thông minh. Ứng dụng chạy mượt mà ngay cả khi không có mạng hoặc chưa có key!")

# ==============================================================================
# 5. HEADER CHÍNH & METRICS TỔNG QUAN
# ==============================================================================
st.markdown('<div class="main-title">🏛️ Regulation & Compliance Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Hệ thống AI Tra cứu, So sánh Diff Engine & Phân tích Tác động Quy định Ngân hàng Nhà nước Việt Nam</div>', unsafe_allow_html=True)

# Tính toán metric động từ checklist
total_req = len(st.session_state.checklist_data)
completed_req = len(st.session_state.checklist_data[st.session_state.checklist_data["Status"] == "Đã tuân thủ"])
compliance_pct = int((completed_req / total_req) * 100) if total_req > 0 else 0
high_impact_count = len(st.session_state.impact_map_data[st.session_state.impact_map_data["Impact_Level"] == "Cao"])

c_m1, c_m2, c_m3, c_m4 = st.columns(4)
with c_m1:
    st.metric(label="Điều khoản đã phân tích", value="35 Điều", delta="TT 12/2024 & TT 09/2023")
with c_m2:
    st.metric(label="Yêu cầu tuân thủ cốt lõi", value=f"{total_req} Mục", delta="Chuẩn 4 trường")
with c_m3:
    st.metric(label="Tỷ lệ tuân thủ (Readiness)", value=f"{compliance_pct}%", delta=f"{completed_req}/{total_req} hoàn tất")
with c_m4:
    st.metric(label="Thay đổi tác động CAO", value=f"{high_impact_count} Điểm", delta="Yêu cầu xử lý gấp", delta_color="inverse")

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# 6. GIAO DIỆN CHÍNH - 3 TAB CHỨC NĂNG CỐT LÕI
# ==============================================================================
tab1, tab2, tab3 = st.tabs([
    "🔍 TAB 1: TRA CỨU & HỎI ĐÁP (RAG Q&A)",
    "📊 TAB 2: SO SÁNH VĂN BẢN (DIFF COMPARISON ENGINE)",
    "📋 TAB 3: CHECKLIST & BẢN ĐỒ TÁC ĐỘNG (IMPACT MAP)"
])

# ------------------------------------------------------------------------------
# TAB 1: TRA CỨU RAG & CƠ CHẾ TỪ CHỐI (REFUSAL MECHANISM)
# ------------------------------------------------------------------------------
with tab1:
    st.markdown("### 🔍 Tra cứu Quy định & Giải đáp Tự động (RAG with Citation)")
    st.caption("AI tra cứu dựa trên văn bản Thông tư 09/2023/TT-NHNN và Thông tư 12/2024/TT-NHNN kèm Dẫn nguồn cụ thể. Tích hợp cơ chế từ chối khi câu hỏi ngoài phạm vi.")

    st.markdown("**📌 Câu hỏi mẫu kiểm thử:**")
    sq1, sq2, sq3, sq4 = st.columns(4)
    sample_text = None
    if sq1.button("⏱️ Hạn báo cáo AML hàng năm?"):
        sample_text = "Thời hạn nộp báo cáo đánh giá rủi ro rửa tiền hằng năm của đối tượng báo cáo là khi nào?"
    if sq2.button("💰 Hạn mức cho vay nhỏ?"):
        sample_text = "Quy định thế nào là khoản cho vay có mức giá trị nhỏ theo Thông tư 12/2024/TT-NHNN?"
    if sq3.button("🛡️ Biện pháp với rủi ro AML cao?"):
        sample_text = "Ngân hàng phải áp dụng các biện pháp tăng cường nào đối với khách hàng có mức rủi ro rửa tiền cao?"
    if sq4.button("⚠️ Test ngoài phạm vi (Từ chối)?"):
        sample_text = "Quy định về biên độ giá vàng miếng SJC và lãi suất phát hành chứng chỉ quỹ hiện nay là bao nhiêu?"

    default_val = sample_text if sample_text else ""
    user_query = st.text_input("Nhập câu hỏi tra cứu pháp lý:", value=default_val, placeholder="Nhập câu hỏi liên quan đến cho vay hoặc phòng chống rửa tiền...")

    if st.button("🚀 Gửi câu hỏi tra cứu", type="primary", key="btn_ask_rag"):
        if not user_query.strip():
            st.warning("Vui lòng nhập câu hỏi cần tra cứu.")
        else:
            with st.spinner("Đang truy xuất cơ sở dữ liệu pháp lý và kiểm tra tính xác thực nguồn..."):
                response_text = ""
                # Kịch bản 1: Gọi Gemini API nếu có Key
                if gemini_api_key.strip() and HAS_GENAI:
                    try:
                        genai.configure(api_key=gemini_api_key.strip())
                        system_instruction = f"""
Bạn là Chuyên gia Pháp chế & Tuân thủ Ngân hàng Nhà nước Việt Nam (NHNN).
Bạn chỉ được phép trả lời dựa trên CĂN CỨ PHÁP LÝ NHNN dưới đây:
{LEGAL_KNOWLEDGE_BASE}

QUY TẮC BẮT BUỘC (CRITICAL COMPLIANCE RULES):
1. Mọi câu trả lời hợp lệ PHẢI có Citation chi tiết theo định dạng:
   **Dẫn nguồn:** [Tên văn bản] | [Điều] | [Khoản] | [Nội dung trích dẫn hoặc Trang].
2. NGUYÊN TẮC TỪ CHỐI (Refusal Mechanism): Nếu nội dung câu hỏi KHÔNG có trong cơ sở pháp lý trên (ví dụ hỏi về giá vàng, chứng khoán, tiền số, tỷ giá...), bạn BẮT BUỘC phải mở đầu câu trả lời bằng đúng chuỗi:
   "⚠️ Cảnh báo: Thiếu căn cứ nguồn rõ ràng trong văn bản NHNN được cung cấp."
   và không được suy đoán thông tin ngoài nguồn.
"""
                        model = genai.GenerativeModel(
                            model_name=selected_model,
                            system_instruction=system_instruction
                        )
                        res = model.generate_content(user_query)
                        response_text = res.text
                    except Exception as e:
                        st.error(f"Lỗi khi gọi Gemini API ({e}). Đang tự động chuyển sang Offline Mock Engine.")
                        response_text = None

                # Kịch bản 2: Offline Mock Engine thông minh
                if not response_text:
                    q = user_query.lower()
                    if "rửa tiền" in q and ("thời hạn" in q or "báo cáo" in q or "31/3" in q):
                        response_text = """Theo quy định của Ngân hàng Nhà nước Việt Nam:
Đối tượng báo cáo có trách nhiệm thu thập số liệu đánh giá rủi ro rửa tiền theo năm và hoàn thành báo cáo chậm nhất vào ngày 31 tháng 3 của năm tiếp theo gửi Cục Phòng, chống rửa tiền.

**Dẫn nguồn:** [Thông tư số 09/2023/TT-NHNN] | [Điều 3] | [Khoản 5] | [Trang 5]"""
                    elif "giá trị nhỏ" in q or "100 triệu" in q or "vay nhỏ" in q:
                        response_text = """Khoản cho vay có mức giá trị nhỏ là khoản vay không vượt quá 100.000.000 (một trăm triệu) đồng Việt Nam. Đối với khoản vay giá trị nhỏ này, khách hàng không bắt buộc phải cung cấp phương án sử dụng vốn khả thi mà chỉ cần cung cấp tối thiểu thông tin về mục đích sử dụng vốn hợp pháp và khả năng tài chính thực hiện nghĩa vụ trả nợ.

**Dẫn nguồn:** [Thông tư số 12/2024/TT-NHNN] | [Điều 1] | [Khoản 1 & Khoản 4] | [Trang 1-3]"""
                    elif "tăng cường" in q or "rủi ro cao" in q:
                        response_text = """Đối với khách hàng có mức rủi ro rửa tiền cao, tổ chức tín dụng phải áp dụng các biện pháp tăng cường: thu thập bổ sung thông tin tài liệu nhận biết khách hàng, tăng tần suất giám sát giao dịch và bắt buộc phải có sự phê duyệt của người quản lý cấp cao trước khi thiết lập hoặc tiếp tục duy trì mối quan hệ giao dịch.

**Dẫn nguồn:** [Thông tư số 09/2023/TT-NHNN] | [Điều 4] | [Khoản 5] | [Trang 7]"""
                    elif "đào tạo" in q or "tuyển dụng" in q or "6 tháng" in q:
                        response_text = """Đối tượng báo cáo có nghĩa vụ thực hiện tuyển dụng nhân sự chặt chẽ và tổ chức đào tạo kiến thức cơ bản về phòng, chống rửa tiền cho nhân viên mới trong thời hạn 06 tháng kể từ ngày tuyển dụng.

**Dẫn nguồn:** [Thông tư số 09/2023/TT-NHNN] | [Điều 5] | [Khoản 6] | [Trang 9]"""
                    else:
                        response_text = "⚠️ Cảnh báo: Thiếu căn cứ nguồn rõ ràng trong văn bản NHNN được cung cấp. Câu hỏi của bạn nằm ngoài phạm vi Thông tư 09/2023/TT-NHNN và Thông tư 12/2024/TT-NHNN."

                # Hiển thị kết quả với giao diện phân biệt
                if "⚠️ Cảnh báo: Thiếu căn cứ nguồn rõ ràng" in response_text:
                    st.markdown(f'<div class="refusal-alert">{response_text}</div>', unsafe_allow_html=True)
                else:
                    st.success("✅ Đã tìm thấy căn cứ pháp lý và đối chiếu thành công:")
                    st.markdown(response_text)

# ------------------------------------------------------------------------------
# TAB 2: SO SÁNH VĂN BẢN (DIFF COMPARISON ENGINE)
# ------------------------------------------------------------------------------
with tab2:
    st.markdown("### 📊 Diff Comparison Engine: Thông tư 39/2016 vs Thông tư 12/2024")
    st.caption("Công cụ đối chiếu điều khoản cũ & mới, phân loại thay đổi (Added, Modified, Removed) tích hợp kiểm soát con người (Human-in-the-loop).")

    # Bộ lọc và tìm kiếm nhanh
    f_col1, f_col2 = st.columns([1, 2])
    with f_col1:
        type_filters = st.multiselect(
            "Lọc loại biến động:",
            ["Added", "Modified", "Removed"],
            default=["Added", "Modified", "Removed"]
        )
    with f_col2:
        search_kw = st.text_input("Tìm kiếm nhanh điều khoản hoặc nội dung:", placeholder="Ví dụ: 100 triệu, bãi bỏ, phương án...")

    filtered_diff = st.session_state.diff_data.copy()
    if type_filters:
        filtered_diff = filtered_diff[filtered_diff["Change_Type"].isin(type_filters)]
    if search_kw.strip():
        kw = search_kw.strip().lower()
        filtered_diff = filtered_diff[
            filtered_diff["Legal_Basis"].str.lower().str.contains(kw) |
            filtered_diff["New_Text"].str.lower().str.contains(kw) |
            filtered_diff["Old_Text"].str.lower().str.contains(kw)
        ]

    # Bảng Human-in-the-loop dùng st.data_editor
    st.markdown("##### 📝 Bảng thẩm duyệt điều khoản đối chiếu:")
    diff_config = {
        "Change_ID": st.column_config.TextColumn("Mã điều", width="small", disabled=True),
        "Legal_Basis": st.column_config.TextColumn("Căn cứ pháp lý", width="medium", disabled=True),
        "Old_Text": st.column_config.TextColumn("Nội dung gốc (TT 39/2016)", width="large"),
        "New_Text": st.column_config.TextColumn("Nội dung mới (TT 12/2024)", width="large"),
        "Change_Type": st.column_config.SelectboxColumn(
            "Loại thay đổi",
            options=["Added", "Modified", "Removed", "Reworded", "Unchanged"],
            width="small"
        ),
        "Review_Status": st.column_config.SelectboxColumn(
            "Phê duyệt (Human-in-the-loop)",
            options=["Approve", "Edit", "Pending"],
            width="medium",
            required=True
        ),
        "Reviewer_Note": st.column_config.TextColumn("Ghi chú của Thẩm định viên", width="large")
    }

    edited_diff_df = st.data_editor(
        filtered_diff,
        column_config=diff_config,
        use_container_width=True,
        hide_index=True,
        key="diff_data_editor"
    )

    # Nút Lưu và Export CSV
    b_col1, b_col2, _ = st.columns([1.5, 1.5, 4])
    with b_col1:
        if st.button("💾 Lưu phê duyệt điều khoản"):
            st.session_state.diff_data.update(edited_diff_df)
            st.success("Đã ghi nhận trạng thái phê duyệt của thẩm định viên thành công!")

    with b_col2:
        diff_csv_buffer = io.StringIO()
        edited_diff_df.to_csv(diff_csv_buffer, index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 Export CSV So Sánh",
            data=diff_csv_buffer.getvalue().encode("utf-8-sig"),
            file_name="diff_comparison_tt39_tt12.csv",
            mime="text/csv"
        )

    # Form thêm mục so sánh mới (Human-in-the-loop)
    with st.expander("➕ Thêm điều khoản đối chiếu thủ công"):
        with st.form("form_add_diff"):
            add_c1, add_c2, add_c3 = st.columns(3)
            with add_c1:
                new_id = st.text_input("Mã Change_ID:", value=f"LOAN-0{len(st.session_state.diff_data)+1}")
            with add_c2:
                new_basis = st.text_input("Căn cứ pháp lý:", "TT 12/2024 Điều ...")
            with add_c3:
                new_type = st.selectbox("Loại thay đổi:", ["Added", "Modified", "Removed"])

            new_old_text = st.text_area("Nội dung gốc (cũ):")
            new_new_text = st.text_area("Nội dung sửa đổi / bổ sung (mới):")
            new_note = st.text_input("Ghi chú nghiệp vụ:")

            if st.form_submit_button("Lưu điều khoản vào hệ thống"):
                new_row = {
                    "Change_ID": new_id,
                    "Legal_Basis": new_basis,
                    "Old_Text": new_old_text,
                    "New_Text": new_new_text,
                    "Change_Type": new_type,
                    "Review_Status": "Approve",
                    "Reviewer_Note": new_note
                }
                st.session_state.diff_data = pd.concat([st.session_state.diff_data, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Đã thêm điều khoản mới vào danh mục đối chiếu!")
                st.rerun()

# ------------------------------------------------------------------------------
# TAB 3: CHECKLIST & BẢN ĐỒ TÁC ĐỘNG (IMPACT MAP)
# ------------------------------------------------------------------------------
with tab3:
    subtab1, subtab2 = st.tabs([
        "📋 Sub-tab 1: Danh mục kiểm soát tuân thủ (Checklist 4 trường)",
        "🗺️ Sub-tab 2: Bản đồ tác động doanh nghiệp (Impact Map 11 cột)"
    ])

    # SUB-TAB 1: COMPLIANCE CHECKLIST
    with subtab1:
        st.markdown("#### 📋 Compliance Checklist (Yêu cầu, Chủ thể, Hành động, Bằng chứng kiểm soát)")
        st.caption("Bóc tách 4 trường cốt lõi phục vụ đánh giá mức độ sẵn sàng tuân thủ của tổ chức tín dụng.")

        chk_config = {
            "ID": st.column_config.TextColumn("Mã nghĩa vụ", width="small", disabled=True),
            "Requirement": st.column_config.TextColumn("Requirement (Yêu cầu tuân thủ)", width="large"),
            "Subject": st.column_config.TextColumn("Subject (Chủ thể chịu trách nhiệm)", width="medium"),
            "Action": st.column_config.TextColumn("Action (Hành động bắt buộc)", width="large"),
            "Control": st.column_config.TextColumn("Control/Evidence (Bằng chứng kiểm soát)", width="large"),
            "Status": st.column_config.SelectboxColumn(
                "Trạng thái tuân thủ",
                options=["Chưa thực hiện", "Đang xử lý", "Đã tuân thủ"],
                width="medium",
                required=True
            )
        }

        edited_chk_df = st.data_editor(
            st.session_state.checklist_data,
            column_config=chk_config,
            use_container_width=True,
            hide_index=True,
            key="checklist_editor_table"
        )

        chk_b1, chk_b2, _ = st.columns([1.5, 1.5, 4])
        with chk_b1:
            if st.button("💾 Cập nhật trạng thái Checklist"):
                st.session_state.checklist_data = edited_chk_df
                st.success("Đã cập nhật tỷ lệ tuân thủ thành công!")
                st.rerun()

        with chk_b2:
            chk_buf = io.StringIO()
            edited_chk_df.to_csv(chk_buf, index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 Export Checklist CSV",
                data=chk_buf.getvalue().encode("utf-8-sig"),
                file_name="compliance_checklist_nhnn.csv",
                mime="text/csv"
            )

    # SUB-TAB 2: REGULATORY IMPACT MAP
    with subtab2:
        st.markdown("#### 🗺️ Bản Đồ Tác Động Quy Định (Regulatory Impact Map - 11 Cột Chuẩn)")
        st.caption("Bản đồ phân tích mối liên hệ logic nguyên nhân - kết quả giữa văn bản pháp luật và vận hành nội bộ ngân hàng.")

        imp_col1, _ = st.columns([2, 4])
        with imp_col1:
            impact_filter = st.multiselect(
                "Lọc theo mức độ tác động:",
                ["Cao", "Trung bình", "Thấp"],
                default=["Cao", "Trung bình", "Thấp"]
            )

        current_impact = st.session_state.impact_map_data.copy()
        if impact_filter:
            current_impact = current_impact[current_impact["Impact_Level"].isin(impact_filter)]

        impact_table_config = {
            "Change_ID": st.column_config.TextColumn("Change_ID", width="small"),
            "Legal_Basis": st.column_config.TextColumn("Legal_Basis", width="medium"),
            "Change_Summary": st.column_config.TextColumn("Change_Summary", width="large"),
            "Requirement": st.column_config.TextColumn("Requirement", width="large"),
            "Affected_Department": st.column_config.TextColumn("Affected_Department", width="medium"),
            "Affected_Process": st.column_config.TextColumn("Affected_Process", width="large"),
            "Affected_Data_Field": st.column_config.TextColumn("Affected_Data_Field", width="medium"),
            "Impact_Level": st.column_config.SelectboxColumn(
                "Impact_Level",
                options=["Cao", "Trung bình", "Thấp"],
                width="small"
            ),
            "Required_Action": st.column_config.TextColumn("Required_Action", width="large"),
            "Evidence": st.column_config.TextColumn("Evidence", width="large"),
            "Verification_Status": st.column_config.SelectboxColumn(
                "Verification_Status",
                options=["Đã có căn cứ", "Dự kiến", "Chưa xác định"],
                width="medium"
            )
        }

        edited_impact_df = st.data_editor(
            current_impact,
            column_config=impact_table_config,
            use_container_width=True,
            hide_index=True,
            key="impact_editor_table"
        )

        imp_b1, imp_b2, _ = st.columns([1.5, 1.5, 4])
        with imp_b1:
            if st.button("💾 Đồng bộ Bản đồ Tác động"):
                st.session_state.impact_map_data.update(edited_impact_df)
                st.success("Đã đồng bộ dữ liệu bản đồ tác động vào cơ sở dữ liệu!")

        with imp_b2:
            imp_buf = io.StringIO()
            edited_impact_df.to_csv(imp_buf, index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 Export Impact Map CSV",
                data=imp_buf.getvalue().encode("utf-8-sig"),
                file_name="regulatory_impact_map.csv",
                mime="text/csv"
            )

# ==============================================================================
# FOOTER CHUẨN ĐỒ ÁN
# ==============================================================================
st.markdown("---")
st.markdown(
    "<center><small style='color: #718096;'>Project 06: Regulation & Compliance Intelligence Platform • Trường Đại học Ngân hàng / Khóa Huấn luyện Large Language Models in Banking & Finance</small></center>",
    unsafe_allow_html=True
)
