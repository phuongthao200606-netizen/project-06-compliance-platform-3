import io
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Kiểm tra thư viện Gemini API
try:
  import google.generativeai as genai

  HAS_GEMINI = True
except ImportError:
  HAS_GEMINI = False

# ==============================================================================
# 1. CẤU HÌNH GIAO DIỆN RỰC RỠ & SẮC MÀU (FINTECH DASHBOARD)
# ==============================================================================
st.set_page_config(
    page_title="Project 06 - NHNN RegTech Platform", page_icon="🏛️", layout="wide"
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    /* Header Gradient */
    .header-box {
        background: linear-gradient(135deg, #0F2A4A 0%, #1A365D 50%, #2B6CB0 100%);
        padding: 24px;
        border-radius: 16px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(15, 42, 74, 0.3);
    }
    .main-title {
        color: #FFFFFF;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 0.3rem;
    }
    .sub-title {
        color: #E2E8F0;
        font-size: 1.05rem;
    }
    
    /* Metric Card Styling */
    .metric-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        border-left: 6px solid #3182CE;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    
    /* Alert Boxes */
    .refusal-alert {
        background-color: #FFF5F5;
        border-left: 6px solid #E53E3E;
        color: #C53030;
        padding: 16px 20px;
        border-radius: 10px;
        font-weight: 600;
        margin-top: 15px;
        box-shadow: 0 4px 6px -1px rgba(229, 62, 62, 0.1);
    }
    .citation-box {
        background-color: #EBF8FF;
        border-left: 6px solid #3182CE;
        padding: 14px 18px;
        border-radius: 8px;
        color: #2B6CB0;
        font-size: 0.95rem;
        margin-top: 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. KHỞI TẠO STATE & DỮ LIỆU BAN ĐẦU
# ==============================================================================
if "user_query" not in st.session_state:
  st.session_state.user_query = ""

LEGAL_KB = """
[CĂN CỨ PHÁP LÝ NHNN]
1. Thông tư số 09/2023/TT-NHNN (Hướng dẫn thực hiện Luật Phòng, chống rửa tiền):
- Điều 3 khoản 4: Phương pháp chấm điểm để đánh giá rủi ro rửa tiền và mức độ phù hợp của chính sách nội bộ (Trang 4-5).
- Điều 3 khoản 5: Thu thập dữ liệu đánh giá rủi ro theo năm và hoàn thành báo cáo chậm nhất ngày 31/3 năm tiếp theo gửi Cục PCRT (Trang 5).
- Điều 4 khoản 1: Đối tượng báo cáo xây dựng quy trình quản lý rủi ro rửa tiền và phân loại khách hàng theo 3 mức độ rủi ro (Trang 6).
- Điều 4 khoản 5: Áp dụng các biện pháp tăng cường đối với khách hàng có mức rủi ro rửa tiền cao (Trang 7).

2. Thông tư số 12/2024/TT-NHNN (Sửa đổi, bổ sung Thông tư số 39/2016/TT-NHNN về hoạt động cho vay):
- Điều 1 khoản 1: Khoản cho vay có mức giá trị nhỏ là khoản vay không vượt quá 100.000.000 (một trăm triệu) đồng Việt Nam (Trang 1).
- Điều 1 khoản 4: Khoản vay nhỏ dưới 100 triệu không bắt buộc phải có phương án sử dụng vốn khả thi, chỉ cần thông tin tối thiểu về mục đích hợp pháp (Trang 2-3).
- Điều 2: Bãi bỏ hiệu lực của Điều 29, Điều 32 và Điều 32g Thông tư 39/2016/TT-NHNN (Trang 5).
"""

if "diff_data" not in st.session_state:
  st.session_state.diff_data = pd.DataFrame([
      {
          "Change_ID": "LOAN-01",
          "Legal_Basis": "TT 12/2024 Điều 1 Khoản 1",
          "Old_Text": "(Chưa quy định hạn mức định lượng riêng)",
          "New_Text": (
              "Khoản cho vay có giá trị nhỏ không vượt quá 100.000.000 VNĐ."
          ),
          "Change_Type": "Added",
          "Review_Status": True,
      },
      {
          "Change_ID": "LOAN-02",
          "Legal_Basis": "TT 12/2024 Điều 1 Khoản 4",
          "Old_Text": (
              "Mọi khoản vay bắt buộc phải có phương án sử dụng vốn khả thi."
          ),
          "New_Text": (
              "Khoản vay nhỏ (<= 100 triệu) được miễn lập phương án chi tiết."
          ),
          "Change_Type": "Modified",
          "Review_Status": True,
      },
      {
          "Change_ID": "LOAN-03",
          "Legal_Basis": "TT 12/2024 Điều 2",
          "Old_Text": "Quy định thủ tục kiểm soát tại Điều 29, 32.",
          "New_Text": (
              "Chính thức bãi bỏ áp dụng toàn bộ Điều 29, Điều 32 và Điều 32g."
          ),
          "Change_Type": "Removed",
          "Review_Status": True,
      },
  ])

if "checklist_data" not in st.session_state:
  st.session_state.checklist_data = pd.DataFrame([
      {
          "ID": "AML-01",
          "Requirement": (
              "Xây dựng phương pháp chấm điểm rủi ro rửa tiền định lượng."
          ),
          "Subject": "Khối QLRR & Tuân thủ",
          "Action": "Ban hành bảng tiêu chí chấm điểm và ma trận rủi ro.",
          "Control": "Quy chế Quản lý rủi ro rửa tiền.",
          "Status": "Đã tuân thủ",
      },
      {
          "ID": "AML-02",
          "Requirement": (
              "Hoàn thành báo cáo đánh giá rủi ro rửa tiền định kỳ hàng năm."
          ),
          "Subject": "Ban PCRT (AML)",
          "Action": "Nộp báo cáo trước ngày 31/3 năm tiếp theo.",
          "Control": "Báo cáo nộp Cục PCRT có xác nhận.",
          "Status": "Đang xử lý",
      },
      {
          "ID": "LOAN-01",
          "Requirement": (
              "Thiết lập hạn mức và luồng thẩm định khoản vay <= 100 triệu."
          ),
          "Subject": "Khối Tín dụng",
          "Action": "Cấu hình luồng phê duyệt riêng trên hệ thống LOS.",
          "Control": "Biên bản nghiệm thu UAT hệ thống LOS.",
          "Status": "Chưa thực hiện",
      },
      {
          "ID": "AML-05",
          "Requirement": "Đào tạo kiến thức cơ bản về PCRT cho nhân sự mới.",
          "Subject": "Khối HR & Tuân thủ",
          "Action": "Đào tạo hoàn thành trong vòng 6 tháng.",
          "Control": "Danh sách điểm danh & bài test.",
          "Status": "Đã tuân thủ",
      },
  ])

if "impact_map_data" not in st.session_state:
  st.session_state.impact_map_data = pd.DataFrame([
      {
          "Change_ID": "LOAN-01",
          "Legal_Basis": "TT 12/2024/TT-NHNN, Điều 1 K1",
          "Change_Summary": "Khái niệm khoản vay nhỏ <= 100tr",
          "Requirement": "Luồng thẩm định riêng cho khoản vay nhỏ",
          "Affected_Department": "Khối Tín dụng",
          "Affected_Process": "Quy trình Phê duyệt Khoản vay",
          "Affected_Data_Field": "Is_Small_Loan",
          "Impact_Level": "Cao",
      },
      {
          "Change_ID": "LOAN-02",
          "Legal_Basis": "TT 12/2024/TT-NHNN, Điều 1 K4",
          "Change_Summary": "Miễn lập phương án dùng vốn khoản vay nhỏ",
          "Requirement": "Rút gọn hồ sơ thủ tục vay",
          "Affected_Department": "Khối Tín dụng",
          "Affected_Process": "Thẩm định Hồ sơ Vay vốn",
          "Affected_Data_Field": "Capital_Use_Doc",
          "Impact_Level": "Trung bình",
      },
      {
          "Change_ID": "AML-02",
          "Legal_Basis": "TT 09/2023/TT-NHNN, Điều 3 K5",
          "Change_Summary": "Hạn nộp báo cáo rủi ro AML là 31/3",
          "Requirement": "Nộp báo cáo rủi ro định kỳ đúng hạn",
          "Affected_Department": "Khối Tuân thủ",
          "Affected_Process": "Quy trình Báo cáo AML Hằng năm",
          "Affected_Data_Field": "Annual_Report_Date",
          "Impact_Level": "Cao",
      },
      {
          "Change_ID": "LOAN-05",
          "Legal_Basis": "TT 12/2024/TT-NHNN, Điều 2",
          "Change_Summary": "Bãi bỏ Điều 29, 32 và 32g",
          "Requirement": "Bãi bỏ thủ tục báo cáo cũ",
          "Affected_Department": "Khối Tuân thủ",
          "Affected_Process": "Báo cáo Định kỳ NHNN",
          "Affected_Data_Field": "N/A",
          "Impact_Level": "Thấp",
      },
  ])

# ==============================================================================
# 3. THANH SIDEBAR & KẾT NỐI GEMINI API
# ==============================================================================
with st.sidebar:
  st.markdown("### 🏛️ NHNN RegTech Platform")
  st.markdown("**Project 06: Compliance AI Platform**")
  st.markdown("---")
  st.markdown("#### 👥 Đội ngũ thực hiện (Team 01)")
  st.markdown("""
    - **Leader:** Phương Thảo
    - **Thành viên:** Bảo Châu, Thúy Hiền, Như Ý, Minh Anh, Ánh Ngọc
    """)
  st.markdown("---")
  st.markdown("#### ⚙️ Cấu hình Gemini API Key")
  gemini_api_key = st.text_input(
      "Dán Gemini API Key", type="password", placeholder="AIzaSy..."
  )
  model_choice = st.selectbox(
      "Chọn mô hình Gemini", ["gemini-1.5-flash", "gemini-1.5-pro"]
  )

  api_active = False
  if gemini_api_key and HAS_GEMINI:
    try:
      genai.configure(api_key=gemini_api_key)
      model = genai.GenerativeModel(model_choice)
      api_active = True
      st.success("⚡ Kết nối Gemini API thành công!")
    except Exception as e:
      st.error(f"Lỗi API: {e}")
  else:
    st.info("💡 Chạy ở chế độ Offline Fallback Engine.")

# ==============================================================================
# 4. HEADER RỰC RỠ & METRIC CARDS TỔNG QUAN
# ==============================================================================
st.markdown(
    """
<div class="header-box">
    <div class="main-title">🏛️ Regulation & Compliance Intelligence Platform</div>
    <div class="sub-title">Hệ thống AI Tra cứu, So sánh Diff Engine & Phân tích Tác động Quy định Ngân hàng Nhà nước</div>
</div>
""",
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
with m1:
  st.metric("Văn bản phân tích", "35 Điều khoản", "TT 12/2024 & TT 09/2023")
with m2:
  st.metric(
      "Yêu cầu tuân thủ",
      f"{len(st.session_state.checklist_data)} Mục",
      "Ghi nhận mới",
  )
with m3:
  completed = len(
      st.session_state.checklist_data[
          st.session_state.checklist_data["Status"] == "Đã tuân thủ"
      ]
  )
  pct = (
      int((completed / len(st.session_state.checklist_data)) * 100)
      if len(st.session_state.checklist_data) > 0
      else 0
  )
  st.metric(
      "Tỷ lệ hoàn thành",
      f"{pct}%",
      f"{completed}/{len(st.session_state.checklist_data)} mục",
  )
with m4:
  high_cnt = len(
      st.session_state.impact_map_data[
          st.session_state.impact_map_data["Impact_Level"] == "Cao"
      ]
  )
  st.metric(
      "Tác động mức CAO", f"{high_cnt} Điểm", "Ưu tiên", delta_color="inverse"
  )

st.write("")

# ==============================================================================
# 5. CÁC TAB CHỨC NĂNG VÀ HỆ THỐNG BIỂU ĐỒ PHÂN TÍCH
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 TAB 1: TRA CỨU & HỎI ĐÁP (RAG Q&A)",
    "📊 TAB 2: SO SÁNH VĂN BẢN (DIFF COMPARISON)",
    "📋 TAB 3: CHECKLIST & BẢN ĐỒ TÁC ĐỘNG",
    "📈 TAB 4: BIỂU ĐỒ PHÂN TÍCH QUẢN TRỊ",
])

# ------------------------------------------------------------------------------
# TAB 1: TRA CỨU RAG CÓ SỬA LỖI STATE
# ------------------------------------------------------------------------------
with tab1:
  st.markdown("#### 🔍 Tra cứu Quy định & Giải đáp Tự động (RAG with Citation)")
  st.caption(
      "AI tra cứu dựa trên văn bản Thông tư 09/2023/TT-NHNN và Thông tư"
      " 12/2024/TT-NHNN."
  )

  st.markdown("**📌 Câu hỏi mẫu kiểm thử (Click để điền nhanh):**")
  c1, c2, c3, c4 = st.columns(4)

  def set_query(q):
    st.session_state.user_query = q

  c1.button(
      "⏱️ Hạn báo cáo AML hàng năm?",
      on_click=set_query,
      args=("Thời hạn nộp báo cáo đánh giá rủi ro rửa tiền là khi nào?",),
  )
  c2.button(
      "💰 Hạn mức cho vay nhỏ?",
      on_click=set_query,
      args=(
          "Khoản cho vay có giá trị nhỏ theo quy định mới là bao nhiêu tiền?",
      ),
  )
  c3.button(
      "🛡️ Biện pháp rủi ro AML cao?",
      on_click=set_query,
      args=(
          "Biện pháp tăng cường đối với khách hàng có mức rủi ro rửa tiền"
          " cao?",
      ),
  )
  c4.button(
      "⚠️ Test ngoài phạm vi (Từ chối)?",
      on_click=set_query,
      args=(
          "Quy định về lãi suất huy động vàng của ngân hàng thương mại hiện nay"
          " ra sao?",
      ),
  )

  query_input = st.text_input(
      "Nhập câu hỏi tra cứu pháp lý:",
      key="user_query",
      placeholder="Nhập câu hỏi liên quan đến cho vay hoặc phòng chống rửa tiền...",
  )

  if st.button("🚀 Gửi câu hỏi tra cứu", type="primary"):
    if not query_input.strip():
      st.warning("Vui lòng nhập câu hỏi cần tra cứu.")
    else:
      with st.spinner("AI đang truy xuất kiến thức & phân tích..."):
        query_lower = query_input.lower()

        # Refusal Mechanism
        if (
            "vàng" in query_lower
            or "lãi suất" in query_lower
            and "vay" not in query_lower
        ):
          st.markdown(
              '<div class="refusal-alert">⚠️ <b>CƠ CHẾ TỪ CHỐI (REFUSAL'
              ' MECHANISM):</b> Câu hỏi của bạn nằm ngoài phạm vi tri thức'
              ' Thông tư 09/2023 và Thông tư 12/2024. Hệ thống từ chối trả lời'
              ' để tránh sinh thông tin sai lệch (Hallucination).</div>',
              unsafe_allow_html=True,
          )

        # Trả lời qua Gemini API
        elif api_active:
          try:
            prompt = (
                f"Dựa vào tri thức sau:\n{LEGAL_KB}\n\nHãy trả lời câu hỏi"
                f" sau kèm trích dẫn nguồn (Điều, Khoản, Trang):\n{query_input}"
            )
            response = model.generate_content(prompt)
            st.success("✅ Trả lời trực tiếp từ Gemini AI:")
            st.write(response.text)
          except Exception as e:
            st.error(f"Lỗi API: {e}")

        # Fallback RAG
        else:
          if "hạn" in query_lower and "nộp" in query_lower or "aml" in query_lower:
            st.success("✅ Căn cứ pháp lý chính xác:")
            st.markdown(
                "Theo **Thông tư số 09/2023/TT-NHNN**, Điều 3 Khoản 5: Đối"
                " tượng báo cáo thu thập dữ liệu đánh giá rủi ro rửa tiền theo"
                " năm và hoàn thành báo cáo **chậm nhất ngày 31/3 năm tiếp theo**"
                " gửi Cục Phòng, chống rửa tiền."
            )
            st.markdown(
                '<div class="citation-box">📌 <b>Trích dẫn nguồn'
                ' (Citation):</b> Thông tư 09/2023/TT-NHNN - Điều 3, Khoản 5,'
                " Trang 5.</div>",
                unsafe_allow_html=True,
            )
          elif "vay" in query_lower or "100" in query_lower:
            st.success("✅ Căn cứ pháp lý chính xác:")
            st.markdown(
                "Theo **Thông tư số 12/2024/TT-NHNN**, Điều 1 Khoản 1 & Khoản"
                " 4: Khoản cho vay có mức giá trị nhỏ là khoản vay **không"
                " vượt quá 100.000.000 đồng**. Các khoản vay này **không bắt"
                " buộc phải có phương án sử dụng vốn khảthi**."
            )
            st.markdown(
                '<div class="citation-box">📌 <b>Trích dẫn nguồn'
                ' (Citation):</b> Thông tư 12/2024/TT-NHNN - Điều 1 (Khoản 1 &'
                " 4), Trang 1-3.</div>",
                unsafe_allow_html=True,
            )
          else:
            st.info(
                "ℹ️ Đã ghi nhận câu hỏi. Thông tin liên quan nhất từ hệ"
                " thống:\n"
                + LEGAL_KB[:350]
                + "..."
            )

# ------------------------------------------------------------------------------
# TAB 2: SO SÁNH VĂN BẢN (DIFF COMPARISON ENGINE)
# ------------------------------------------------------------------------------
with tab2:
  st.markdown("#### 📊 Bộ máy So sánh Thay đổi Quy định (Diff Engine)")
  st.caption(
      "Phân tích các điều khoản Bổ sung (Added), Sửa đổi (Modified) hoặc Bãi bỏ"
      " (Removed)."
  )

  st.data_editor(
      st.session_state.diff_data,
      column_config={
          "Change_ID": st.column_config.TextColumn("Mã", width="small"),
          "Legal_Basis": "Căn cứ pháp lý",
          "Old_Text": "Nội dung cũ",
          "New_Text": "Nội dung mới",
          "Change_Type": st.column_config.SelectboxColumn(
              "Loại biến động",
              options=["Added", "Modified", "Removed"],
              width="small",
          ),
          "Review_Status": st.column_config.CheckboxColumn("Phê duyệt"),
      },
      hide_index=True,
      use_container_width=True,
  )

# ------------------------------------------------------------------------------
# TAB 3: CHECKLIST & BẢN ĐỒ TÁC ĐỘNG
# ------------------------------------------------------------------------------
with tab3:
  st.markdown("#### 📋 Checklist Tuân thủ & Bản đồ Tác động (Impact Map)")

  sub1, sub2 = st.tabs(
      ["✅ Danh mục Kiểm soát", "🗺️ Bản đồ Tác động Doanh nghiệp"]
  )

  with sub1:
    st.data_editor(
        st.session_state.checklist_data,
        column_config={
            "ID": "Mã",
            "Requirement": "Yêu cầu tuân thủ",
            "Subject": "Bộ phận phụ trách",
            "Status": st.column_config.SelectboxColumn(
                "Trạng thái",
                options=["Đã tuân thủ", "Đang xử lý", "Chưa thực hiện"],
            ),
        },
        hide_index=True,
        use_container_width=True,
    )

  with sub2:
    st.dataframe(
        st.session_state.impact_map_data,
        column_config={
            "Change_ID": "Mã",
            "Legal_Basis": "Căn cứ pháp lý",
            "Affected_Department": "Bộ phận ảnh hưởng",
            "Affected_Process": "Quy trình liên quan",
            "Affected_Data_Field": "Trường dữ liệu",
            "Impact_Level": "Mức độ tác động",
        },
        hide_index=True,
        use_container_width=True,
    )

# ------------------------------------------------------------------------------
# TAB 4: BIỂU ĐỒ PHÂN TÍCH SĨ QUAN MANAGEMENT DASHBOARD (MỚI BỔ SUNG)
# ------------------------------------------------------------------------------
with tab4:
  st.markdown("#### 📈 Dashboard Biểu đồ Phân tích Quản trị & Tác động")
  st.caption("Tổng hợp dữ liệu tuân thủ dưới dạng đồ họa trực quan sinh động.")

  col_chart1, col_chart2 = st.columns(2)

  with col_chart1:
    st.markdown("##### 1. Tỷ lệ Trạng thái Tuân thủ (Checklist)")
    status_counts = (
        st.session_state.checklist_data["Status"]
        .value_counts()
        .reset_index()
    )
    status_counts.columns = ["Trạng thái", "Số lượng"]

    fig_pie = px.pie(
        status_counts,
        values="Số lượng",
        names="Trạng thái",
        hole=0.45,
        color="Trạng thái",
        color_discrete_map={
            "Đã tuân thủ": "#38A169",
            "Đang xử lý": "#DD6B20",
            "Chưa thực hiện": "#E53E3E",
        },
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie.update_layout(
        margin=dict(t=20, b=20, l=20, r=20), height=320, showlegend=False
    )
    st.plotly_chart(fig_pie, use_container_width=True)

  with col_chart2:
    st.markdown("##### 2. Phân bổ Mức độ Tác động Quy định (Impact Map)")
    impact_counts = (
        st.session_state.impact_map_data["Impact_Level"]
        .value_counts()
        .reset_index()
    )
    impact_counts.columns = ["Mức độ", "Số lượng"]

    fig_bar = px.bar(
        impact_counts,
        x="Mức độ",
        y="Số lượng",
        color="Mức độ",
        text="Số lượng",
        color_discrete_map={
            "Cao": "#E53E3E",
            "Trung bình": "#D69E2E",
            "Thấp": "#3182CE",
        },
    )
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        height=320,
        yaxis=dict(title="Số lượng điểm thay đổi"),
        showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

  st.markdown("##### 3. Số lượng Quy định Tác động theo Khối/Phòng Ban")
  dept_counts = (
      st.session_state.impact_map_data["Affected_Department"]
      .value_counts()
      .reset_index()
  )
  dept_counts.columns = ["Khối/Phòng ban", "Số tác động"]

  fig_dept = px.bar(
      dept_counts,
      y="Khối/Phòng ban",
      x="Số tác động",
      orientation="h",
      color="Số tác động",
      color_continuous_scale="Blues",
  )
  fig_dept.update_layout(
      margin=dict(t=10, b=10, l=10, r=10), height=250, coloraxis_showscale=False
  )
  st.plotly_chart(fig_dept, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #718096; font-size: 0.85rem;'>Project"
    " 06: Regulation & Compliance Intelligence Platform | Phát triển bởi Team"
    " 06</div>",
    unsafe_allow_html=True,
)
