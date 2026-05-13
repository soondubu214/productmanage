import streamlit as st
import pandas as pd
from datetime import date, timedelta

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(page_title="🏠 우리집 재고 관리", layout="centered")

st.title("🏠 우리집 재고 관리")
st.caption("물건을 추가하고, 수량을 관리하고, 유통기한을 체크하세요!")

# ── 세션 상태 초기화 ──────────────────────────────────────────
if "inventory" not in st.session_state:
    st.session_state.inventory = []

# ══════════════════════════════════════════════════════════════
# 1. CSV 업로드
# ══════════════════════════════════════════════════════════════
st.subheader("📂 CSV 파일로 한꺼번에 불러오기")

with st.expander("📋 CSV 형식 안내 (클릭해서 펼치기)"):
    st.markdown("""
**아래 형식으로 엑셀/메모장에서 만들어 저장하세요.**
- 파일 저장 시 형식: `CSV UTF-8` 선택
- 유통기한 형식: `YYYY-MM-DD` (예: 2025-06-01)
""")
    sample_df = pd.DataFrame({
        "물건이름": ["두부", "우유", "샴푸"],
        "수량": [3, 1, 2],
        "유통기한": ["2025-06-01", "2025-05-20", "2026-01-01"]
    })
    st.dataframe(sample_df, use_container_width=True)

    sample_csv = sample_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇️ 샘플 CSV 다운로드",
        data=sample_csv,
        file_name="재고_샘플.csv",
        mime="text/csv"
    )

uploaded_file = st.file_uploader("CSV 파일 선택", type=["csv"])

if uploaded_file is not None:
    try:
        df_upload = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        df_upload.columns = df_upload.columns.str.strip()

        required_cols = {"물건이름", "수량", "유통기한"}
        if not required_cols.issubset(set(df_upload.columns)):
            st.error(f"❌ 열 이름이 올바르지 않아요! '물건이름', '수량', '유통기한' 이 세 가지가 있어야 해요.\n현재 열: {list(df_upload.columns)}")
        else:
            st.dataframe(df_upload, use_container_width=True)
            mode = st.radio("불러오기 방식", ["기존 목록에 추가", "기존 목록 대체"], index=0)
            if st.button("✅ 불러오기", use_container_width=True):
                if mode == "기존 목록 대체":
                    st.session_state.inventory = []

                count = 0
                for _, row in df_upload.iterrows():
                    name = str(row["물건이름"]).strip()
                    qty = int(row["수량"])
                    try:
                        exp = pd.to_datetime(str(row["유통기한"])).date()
                    except Exception:
                        st.warning(f"⚠️ '{name}'의 유통기한 형식이 올바르지 않아요. 오늘 날짜로 대신 입력할게요.")
                        exp = date.today()

                    existing = next(
                        (i for i, x in enumerate(st.session_state.inventory) if x["name"] == name),
                        None
                    )
                    if existing is not None:
                        st.session_state.inventory[existing]["qty"] += qty
                    else:
                        st.session_state.inventory.append({"name": name, "qty": qty, "exp": exp})
                    count += 1

                st.success(f"✅ {count}개 품목을 불러왔어요!")
                st.rerun()

    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했어요: {e}")

st.divider()

# ══════════════════════════════════════════════════════════════
# 2. 물건 직접 추가
# ══════════════════════════════════════════════════════════════
st.subheader("➕ 물건 직접 추가하기")

with st.form("add_item_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        item_name = st.text_input("물건 이름", placeholder="예) 두부, 우유, 샴푸")
    with col2:
        item_qty = st.number_input("수량", min_value=1, max_value=999, value=1)
    with col3:
        item_exp = st.date_input("유통기한", value=date.today() + timedelta(days=30))

    submitted = st.form_submit_button("추가하기", use_container_width=True)

    if submitted:
        if item_name.strip() == "":
            st.error("물건 이름을 입력해 주세요!")
        else:
            existing = next(
                (i for i, x in enumerate(st.session_state.inventory) if x["name"] == item_name.strip()),
                None
            )
            if existing is not None:
                st.session_state.inventory[existing]["qty"] += item_qty
                st.success(f"'{item_name}' 수량을 {item_qty}개 추가했어요!")
            else:
                st.session_state.inventory.append({
                    "name": item_name.strip(),
                    "qty": item_qty,
                    "exp": item_exp,
                })
                st.success(f"'{item_name}'을(를) 목록에 추가했어요!")

st.divider()

# ══════════════════════════════════════════════════════════════
# 3. 재고 현황
# ══════════════════════════════════════════════════════════════
st.subheader("📦 현재 재고 현황")

if len(st.session_state.inventory) == 0:
    st.info("아직 물건이 없어요. 위에서 CSV를 업로드하거나 직접 추가해 보세요! 😊")
else:
    today = date.today()
    warning_days = 7

    for idx, item in enumerate(st.session_state.inventory):
        days_left = (item["exp"] - today).days

        badges = []
        if item["qty"] <= 0:
            badges.append("🔴 재고 없음")
        elif item["qty"] <= 2:
            badges.append("🛒 구매 필요")

        if days_left < 0:
            badges.append("⛔ 유통기한 만료")
        elif days_left <= warning_days:
            badges.append(f"⚠️ 주의 (D-{days_left})")
        else:
            badges.append(f"✅ D-{days_left}")

        badge_str = "  ".join(badges)

        col_name, col_qty, col_minus, col_delete = st.columns([3, 1, 1, 1])

        with col_name:
            st.markdown(f"**{item['name']}**  \n{badge_str}")
        with col_qty:
            qty_color = "red" if item["qty"] <= 2 else "green"
            st.markdown(
                f"<h3 style='color:{qty_color}; margin:0'>{item['qty']}개</h3>",
                unsafe_allow_html=True,
            )
        with col_minus:
            if st.button("－1", key=f"minus_{idx}", use_container_width=True):
                if item["qty"] > 0:
                    st.session_state.inventory[idx]["qty"] -= 1
                    st.rerun()
                else:
                    st.warning("이미 0개예요!")
        with col_delete:
            if st.button("🗑️", key=f"del_{idx}", use_container_width=True):
                st.session_state.inventory.pop(idx)
                st.rerun()

        st.divider()

    # ── 요약 통계 ──────────────────────────────────────────────
    st.subheader("📊 요약")
    total_items = len(st.session_state.inventory)
    need_buy = sum(1 for x in st.session_state.inventory if x["qty"] <= 2)
    exp_warn = sum(
        1 for x in st.session_state.inventory
        if 0 <= (x["exp"] - today).days <= warning_days
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("전체 품목 수", f"{total_items}개")
    c2.metric("구매 필요 품목", f"{need_buy}개")
    c3.metric("유통기한 주의", f"{exp_warn}개")

    # ── CSV 내보내기 ───────────────────────────────────────────
    st.divider()
    df_export = pd.DataFrame([
        {"물건이름": x["name"], "수량": x["qty"], "유통기한": x["exp"]}
        for x in st.session_state.inventory
    ])
    csv_out = df_export.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 현재 재고 CSV로 저장",
        data=csv_out,
        file_name="우리집_재고.csv",
        mime="text/csv"
    )
