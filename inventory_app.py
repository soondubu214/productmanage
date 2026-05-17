import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="🏠 우리집 재고 관리", layout="centered")

st.title("🏠 우리집 재고 관리")
st.caption("물건을 추가하고, 수량을 관리하고, 유통기한을 체크하세요!")

CATEGORIES = {
    "미용":  {"warning_days": 30},
    "팬트리": {"warning_days": 7},
    "냉장고": {"warning_days": 3},
}
CATEGORY_NAMES = list(CATEGORIES.keys())

if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "editing" not in st.session_state:
    st.session_state.editing = {}

st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] { align-items: center; margin-top: -0.3rem; margin-bottom: -0.3rem; }
div[data-testid="stButton"] button { padding: 0.1rem 0.35rem; font-size: 0.80rem; }
hr { margin: 0.25rem 0 !important; }
.item-name {
    font-size: 0.90rem;
    font-weight: bold;
    margin: 0;
    line-height: 1.3;
}
.item-badge {
    font-size: 0.70rem;
    color: gray;
    margin: 0;
    line-height: 1.2;
    padding-bottom: 0.1rem;
}
</style>
""", unsafe_allow_html=True)


def render_inventory(category_filter=None, tab_key=""):
    today = date.today()

    if category_filter:
        items = [(i, x) for i, x in enumerate(st.session_state.inventory)
                 if x["category"] == category_filter]
        warning_days = CATEGORIES[category_filter]["warning_days"]
    else:
        items = list(enumerate(st.session_state.inventory))
        warning_days = None

    if not items:
        st.info("아직 물건이 없어요. 아래에서 추가해 보세요! 😊")
        return

    for idx, item in items:
        days_left = (item["exp"] - today).days
        wd = warning_days if warning_days else CATEGORIES[item["category"]]["warning_days"]

        status_badges = []
        if item["qty"] <= 0:
            status_badges.append("🔴 재고 없음")

        if not category_filter:
            status_badges.insert(0, f"[{item['category']}]")

        status_str = "  ".join(status_badges)

        if days_left < 0 or days_left <= wd:
            name_prefix = "⚠️ "
        else:
            name_prefix = ""

        exp_text = item["exp"].strftime("%Y.%m.%d")
        badge_line = exp_text + ("  " + status_str if status_str else "")
        edit_key = f"{tab_key}_{idx}"
        is_editing = st.session_state.editing.get(edit_key, False)

        col_name, col_qty, col_minus, col_plus, col_edit, col_delete = st.columns([3, 1, 1, 1, 1, 1])

        with col_name:
            if is_editing:
                new_name = st.text_input(
                    "품목명 수정",
                    value=item["name"],
                    key=f"edit_input_{edit_key}",
                    label_visibility="collapsed",
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("저장", key=f"save_{edit_key}", use_container_width=True):
                        if new_name.strip():
                            st.session_state.inventory[idx]["name"] = new_name.strip()
                        st.session_state.editing[edit_key] = False
                        st.rerun()
                with c2:
                    if st.button("취소", key=f"cancel_{edit_key}", use_container_width=True):
                        st.session_state.editing[edit_key] = False
                        st.rerun()
            else:
                st.markdown(
                    f'''<p class="item-name">{name_prefix}{item['name']}</p>
<p class="item-badge">{badge_line}</p>''',
                    unsafe_allow_html=True,
                )

        with col_qty:
            st.markdown(
                f"<p style='color:#333; font-size:0.92rem; font-weight:bold; margin:0.3rem 0 0 0'>{item['qty']}개</p>",
                unsafe_allow_html=True,
            )
        with col_minus:
            if st.button("－", key=f"minus_{tab_key}_{idx}", use_container_width=True):
                if item["qty"] > 0:
                    st.session_state.inventory[idx]["qty"] -= 1
                    st.rerun()
        with col_plus:
            if st.button("＋", key=f"plus_{tab_key}_{idx}", use_container_width=True):
                st.session_state.inventory[idx]["qty"] += 1
                st.rerun()
        with col_edit:
            if st.button("✏️", key=f"edit_btn_{edit_key}", use_container_width=True):
                st.session_state.editing[edit_key] = True
                st.rerun()
        with col_delete:
            if st.button("🗑️", key=f"del_{tab_key}_{idx}", use_container_width=True):
                st.session_state.inventory.pop(idx)
                st.rerun()

        st.divider()


def render_add_form(default_category):
    with st.form(f"add_form_{default_category}", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            item_name = st.text_input("물건 이름", placeholder="예) 토너, 두부, 우유")
        with col2:
            item_qty = st.number_input("수량", min_value=1, max_value=999, value=1)
        with col3:
            item_exp = st.date_input("유통기한", value=date.today() + timedelta(days=30))

        item_category = st.selectbox("대분류", CATEGORY_NAMES,
                                     index=CATEGORY_NAMES.index(default_category))

        submitted = st.form_submit_button("➕ 추가하기", use_container_width=True)
        if submitted:
            if item_name.strip() == "":
                st.error("물건 이름을 입력해 주세요!")
            else:
                existing = next(
                    (i for i, x in enumerate(st.session_state.inventory)
                     if x["name"] == item_name.strip() and x["category"] == item_category),
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
                        "category": item_category,
                    })
                    st.success(f"'{item_name}'을(를) 추가했어요!")


def render_summary(category_filter=None):
    today = date.today()
    items = st.session_state.inventory
    if category_filter:
        items = [x for x in items if x["category"] == category_filter]
    if not items:
        return
    total = len(items)
    out_of_stock = sum(1 for x in items if x["qty"] <= 0)
    exp_warn = sum(
        1 for x in items
        if (x["exp"] - today).days <= CATEGORIES[x["category"]]["warning_days"]
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("전체 품목", f"{total}개")
    c2.metric("재고 없음", f"{out_of_stock}개")
    c3.metric("❕ 유통기한 주의", f"{exp_warn}개")


tab_beauty, tab_pantry, tab_fridge, tab_all, tab_csv = st.tabs([
    "미용", "팬트리", "냉장고", "전체보기", "CSV"
])

with tab_beauty:
    st.subheader("미용")
    st.caption("유통기한 30일 이내 시 주의 표시")
    render_summary("미용")
    st.divider()
    render_inventory("미용", tab_key="beauty")
    st.subheader("➕ 추가하기")
    render_add_form("미용")

with tab_pantry:
    st.subheader("팬트리")
    st.caption("유통기한 7일 이내 시 주의 표시")
    render_summary("팬트리")
    st.divider()
    render_inventory("팬트리", tab_key="pantry")
    st.subheader("➕ 추가하기")
    render_add_form("팬트리")

with tab_fridge:
    st.subheader("냉장고")
    st.caption("유통기한 3일 이내 시 주의 표시")
    render_summary("냉장고")
    st.divider()
    render_inventory("냉장고", tab_key="fridge")
    st.subheader("➕ 추가하기")
    render_add_form("냉장고")

with tab_all:
    st.subheader("전체보기")
    render_summary()
    st.divider()
    render_inventory(tab_key="all")

with tab_csv:
    st.subheader("CSV 파일로 한꺼번에 불러오기")

    with st.expander("CSV 형식 안내 (클릭해서 펼치기)"):
        st.markdown("""
**아래 형식으로 엑셀에서 만들어 CSV UTF-8로 저장하세요.**
- 유통기한 형식: `YYYY-MM-DD` (예: 2025-06-01)
- 대분류: `미용` / `팬트리` / `냉장고`
""")
        sample_df = pd.DataFrame({
            "물건이름": ["토너", "두부", "우유"],
            "수량": [2, 3, 1],
            "유통기한": ["2026-01-01", "2025-06-01", "2025-05-20"],
            "대분류": ["미용", "팬트리", "냉장고"],
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
            required_cols = {"물건이름", "수량", "유통기한", "대분류"}
            if not required_cols.issubset(set(df_upload.columns)):
                st.error(f"❌ 열 이름을 확인해 주세요! 현재 열: {list(df_upload.columns)}")
            else:
                st.dataframe(df_upload, use_container_width=True)
                mode = st.radio("불러오기 방식", ["기존 목록에 추가", "기존 목록 대체"], index=0)
                if st.button("✅ 불러오기", use_container_width=True):
                    if mode == "기존 목록 대체":
                        st.session_state.inventory = []
                    count, skipped = 0, 0
                    for _, row in df_upload.iterrows():
                        # 품목명이 비어있으면 빈 행으로 간주하고 건너뜀
                        raw_name = row["물건이름"]
                        if pd.isna(raw_name) or str(raw_name).strip() == "":
                            continue

                        name = str(raw_name).strip()

                        # 수량: 비어있으면 기본값 1
                        raw_qty = row["수량"]
                        if pd.isna(raw_qty) or str(raw_qty).strip() == "":
                            qty = 1
                        else:
                            try:
                                qty = int(float(str(raw_qty).strip()))
                            except Exception:
                                qty = 1

                        # 대분류
                        raw_cat = row["대분류"]
                        if pd.isna(raw_cat):
                            skipped += 1
                            continue
                        category = str(raw_cat).strip()
                        if category not in CATEGORY_NAMES:
                            skipped += 1
                            continue

                        # 유통기한: 비어있으면 오늘 날짜
                        raw_exp = row["유통기한"]
                        if pd.isna(raw_exp) or str(raw_exp).strip() == "":
                            exp = date.today()
                        else:
                            try:
                                exp = pd.to_datetime(str(raw_exp).strip()).date()
                            except Exception:
                                exp = date.today()

                        existing = next(
                            (i for i, x in enumerate(st.session_state.inventory)
                             if x["name"] == name and x["category"] == category), None
                        )
                        if existing is not None:
                            st.session_state.inventory[existing]["qty"] += qty
                        else:
                            st.session_state.inventory.append({
                                "name": name, "qty": qty, "exp": exp, "category": category
                            })
                        count += 1
                    st.success(f"✅ {count}개 품목을 불러왔어요!" + (f" ({skipped}개 건너뜀)" if skipped else ""))
                    st.rerun()
        except Exception as e:
            st.error(f"파일을 읽는 중 오류가 발생했어요: {e}")

    if st.session_state.inventory:
        st.divider()
        df_export = pd.DataFrame([
            {"물건이름": x["name"], "수량": x["qty"], "유통기한": x["exp"], "대분류": x["category"]}
            for x in st.session_state.inventory
        ])
        csv_out = df_export.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 전체 재고 CSV 저장",
            data=csv_out,
            file_name="우리집_재고.csv",
            mime="text/csv"
        )
