import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="🏠 우리집 재고 관리", layout="centered")

st.title("🏠 우리집 재고 관리")
st.caption("물건을 추가하고, 수량을 관리하고, 유통기한을 체크하세요!")

CATEGORIES = {
    "미용":  {
        "warning_days": 30,
        "subcategories": ["스킨케어","바디케어","헤어케어","메이크업","미용소품","기타"]
    },
    "팬트리": {
        "warning_days": 7,
        "subcategories": ["양념류","장류·오일·식초","가루류","기타"]
    },
    "냉장고": {
        "warning_days": 3,
        "subcategories": ["기타"]
    },
    "냉동실": {
        "warning_days": 90,
        "subcategories": ["채소류","밀프렙","해산물","육류","밀가루","가공식품","기타"]
    },
}
CATEGORY_NAMES = list(CATEGORIES.keys())

if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "editing" not in st.session_state:
    st.session_state.editing = {}
# 중분류 목록을 session_state에 저장 (새로고침 전까지 유지)
if "subcategories" not in st.session_state:
    st.session_state.subcategories = {
        cat: list(info["subcategories"]) for cat, info in CATEGORIES.items()
    }

def get_subs(category):
    """항상 session_state 기준으로 중분류 조회, 가나다 + 기타 맨 뒤"""
    subs = st.session_state.subcategories.get(category, ["기타"])
    non_etc = sorted([s for s in subs if s != "기타"])
    return non_etc + (["기타"] if "기타" in subs else [])

def add_sub(category, new_sub):
    """새 중분류 추가 (중복 방지)"""
    if new_sub and new_sub not in st.session_state.subcategories.get(category, []):
        st.session_state.subcategories.setdefault(category, ["기타"]).append(new_sub)

st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] { align-items: center; margin-top: -0.3rem; margin-bottom: -0.3rem; }
div[data-testid="stButton"] button {
    padding: 0.05rem 0.25rem;
    font-size: 0.75rem;
    line-height: 1.2;
    min-height: 0;
}
hr { margin: 0.25rem 0 !important; }
.item-wrap {
    display: flex;
    flex-direction: column;
    justify-content: center;
    height: 100%;
    padding: 0.15rem 0;
}
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
}
.qty-text {
    display: flex;
    align-items: center;
    height: 100%;
    font-size: 0.88rem;
    font-weight: bold;
    color: #333;
    margin: 0;
}
.subcat-header {
    font-size: 0.78rem;
    font-weight: bold;
    color: #555;
    background: #f5f5f5;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    margin: 0.5rem 0 0.2rem 0;
}
</style>
""", unsafe_allow_html=True)


def render_inventory(category_filter=None, tab_key=""):
    today = date.today()

    if category_filter:
        all_items = [(i, x) for i, x in enumerate(st.session_state.inventory)
                     if x["category"] == category_filter]
        warning_days = CATEGORIES[category_filter]["warning_days"]
        # 실제 데이터에 있는 중분류를 순서 보존하며 동적으로 추출
        # (CATEGORIES에 정의된 순서 먼저, 그 다음 새로 추가된 것)
        defined = get_subs(category_filter)
        actual = list(dict.fromkeys(
            x.get("subcategory", "기타") for _, x in all_items
        ))
        subcats = [s for s in defined if s in actual] + [s for s in actual if s not in defined]
    else:
        all_items = list(enumerate(st.session_state.inventory))
        warning_days = None
        subcats = None

    if not all_items:
        st.info("아직 물건이 없어요. 아래에서 추가해 보세요! 😊")
        return

    def render_row(idx, item, wd):
        days_left = (item["exp"] - today).days if item["exp"] is not None else None

        status_badges = []
        if item["qty"] <= 0:
            status_badges.append("🔴 재고 없음")
        if not category_filter:
            status_badges.insert(0, f"[{item['category']}]")
        status_str = "  ".join(status_badges)

        if item["exp"] is None:
            name_prefix = ""
            exp_text = ""
        elif days_left < 0 or days_left <= wd:
            name_prefix = "⚠️ "
            exp_text = item["exp"].strftime("%Y.%m.%d")
        else:
            name_prefix = ""
            exp_text = item["exp"].strftime("%Y.%m.%d")
        badge_line = exp_text + ("  " + status_str if status_str else "")

        edit_key = f"{tab_key}_{idx}"
        is_editing = st.session_state.editing.get(edit_key, False)

        col_name, col_qty, col_minus, col_plus, col_edit, col_delete = st.columns([3, 1, 1, 1, 1, 1])

        with col_name:
            if is_editing:
                # 품목명
                new_name = st.text_input("품목명", value=item["name"],
                                         key=f"edit_input_{edit_key}",
                                         label_visibility="collapsed")

                # 중분류 — 실제 데이터 기준 전체 목록 + 직접입력
                current_cat = item["category"]
                all_subs = get_subs(current_cat)
                cur_sub = item.get("subcategory", "기타")
                if cur_sub not in all_subs:
                    all_subs = all_subs + [cur_sub]
                sub_options = all_subs + ["직접 입력"]
                cur_sub_idx = all_subs.index(cur_sub) if cur_sub in all_subs else 0
                new_sub_choice = st.selectbox("중분류", sub_options, index=cur_sub_idx,
                                              key=f"edit_sub_{edit_key}")
                if new_sub_choice == "직접 입력":
                    new_sub = st.text_input("중분류 직접 입력", placeholder="예) 음료",
                                            key=f"edit_sub_input_{edit_key}")
                else:
                    new_sub = new_sub_choice

                # 유통기한 — 체크박스로 토글
                has_exp = item["exp"] is not None
                use_exp = st.checkbox("유통기한 입력", value=has_exp,
                                      key=f"edit_use_exp_{edit_key}")
                if use_exp:
                    default_exp = item["exp"] if has_exp else date.today()
                    new_exp = st.date_input("유통기한 날짜", value=default_exp,
                                            key=f"edit_exp_{edit_key}",
                                            label_visibility="collapsed")
                else:
                    new_exp = None

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("저장", key=f"save_{edit_key}", use_container_width=True):
                        if new_name.strip():
                            st.session_state.inventory[idx]["name"] = new_name.strip()
                        final_sub = new_sub.strip() if new_sub_choice == "직접 입력" else new_sub
                        if not final_sub:
                            final_sub = "기타"
                        add_sub(current_cat, final_sub)
                        st.session_state.inventory[idx]["subcategory"] = final_sub
                        st.session_state.inventory[idx]["exp"] = new_exp
                        st.session_state.editing[edit_key] = False
                        st.rerun()
                with c2:
                    if st.button("취소", key=f"cancel_{edit_key}", use_container_width=True):
                        st.session_state.editing[edit_key] = False
                        st.rerun()
            else:
                st.markdown(
                    f'''<div class="item-wrap">
<p class="item-name">{name_prefix}{item["name"]}</p>
<p class="item-badge">{badge_line}</p>
</div>''',
                    unsafe_allow_html=True,
                )

        with col_qty:
            st.markdown(
                f"<div style='display:flex; align-items:center; height:100%;'>"
                f"<p style='color:#333; font-size:0.88rem; font-weight:bold; margin:0;'>{item['qty']}개</p></div>",
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

    # 중분류별 그룹핑 (대분류 탭일 때)
    if subcats and len(subcats) > 1:
        for sub in subcats:
            sub_items = [(i, x) for i, x in all_items if x.get("subcategory", "기타") == sub]
            if not sub_items:
                continue
            wd = warning_days if warning_days else CATEGORIES[sub_items[0][1]["category"]]["warning_days"]
            # 가나다 순 정렬
            sub_items = sorted(sub_items, key=lambda t: t[1]["name"])
            n = len(sub_items)
            with st.expander(f"{sub}  ({n}개)", expanded=True):
                for idx, item in sub_items:
                    render_row(idx, item, wd)
    else:
        # 전체보기: 가나다 순
        sorted_items = sorted(all_items, key=lambda t: (t[1]["category"], t[1].get("subcategory","기타"), t[1]["name"]))
        for idx, item in sorted_items:
            wd = warning_days if warning_days else CATEGORIES[item["category"]]["warning_days"]
            render_row(idx, item, wd)


def render_add_form(default_category):
    # 직접 입력 중분류를 session_state에 미리 보존
    sub_key = f"new_sub_val_{default_category}"
    if sub_key not in st.session_state:
        st.session_state[sub_key] = ""

    col_cat, col_sub = st.columns(2)
    with col_cat:
        item_category = st.selectbox("대분류", CATEGORY_NAMES,
                                     index=CATEGORY_NAMES.index(default_category),
                                     key=f"cat_{default_category}")
    with col_sub:
        subs = get_subs(item_category)
        sub_options = subs + ["직접 입력"]
        sub_choice = st.selectbox("중분류", sub_options, key=f"sub_choice_{default_category}")

    if sub_choice == "직접 입력":
        st.session_state[sub_key] = st.text_input(
            "중분류 직접 입력", value=st.session_state[sub_key],
            placeholder="예) 음료", key=f"new_sub_input_{default_category}"
        )
        item_sub = st.session_state[sub_key]
    else:
        st.session_state[sub_key] = ""
        item_sub = sub_choice

    with st.form(f"add_form_{default_category}", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            item_name = st.text_input("물건 이름", placeholder="예) 토너, 두부, 우유")
        with col2:
            item_qty = st.number_input("수량", min_value=0, max_value=999, value=1)
        with col3:
            use_exp = st.checkbox("유통기한 입력", value=False)
        if use_exp:
            item_exp = st.date_input("유통기한 날짜", value=date.today() + timedelta(days=30),
                                     label_visibility="collapsed")
        else:
            item_exp = None

        submitted = st.form_submit_button("➕ 추가하기", use_container_width=True)
        if submitted:
            if item_name.strip() == "":
                st.error("물건 이름을 입력해 주세요!")
            else:
                final_sub = st.session_state[sub_key] if sub_choice == "직접 입력" else item_sub
                if not final_sub.strip():
                    final_sub = "기타"
                existing = next(
                    (i for i, x in enumerate(st.session_state.inventory)
                     if x["name"] == item_name.strip() and x["category"] == item_category),
                    None
                )
                if existing is not None:
                    st.session_state.inventory[existing]["qty"] += item_qty
                else:
                    add_sub(item_category, final_sub)
                    st.session_state.inventory.append({
                        "name": item_name.strip(),
                        "qty": item_qty,
                        "exp": item_exp,
                        "category": item_category,
                        "subcategory": final_sub,
                    })
                st.session_state[sub_key] = ""
                st.rerun()


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
        if x["exp"] is not None and
        (x["exp"] - today).days <= CATEGORIES[x["category"]]["warning_days"]
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("전체 품목", f"{total}개")
    c2.metric("재고 없음", f"{out_of_stock}개")
    c3.metric("⚠️ 유통기한 주의", f"{exp_warn}개")


# ── 탭 ────────────────────────────────────────────────────────
tab_beauty, tab_pantry, tab_fridge, tab_frozen, tab_all, tab_csv = st.tabs([
    "미용", "팬트리", "냉장고", "냉동실", "전체보기", "CSV"
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

with tab_frozen:
    st.subheader("냉동실")
    st.caption("유통기한 90일 이내 시 주의 표시")
    render_summary("냉동실")
    st.divider()
    render_inventory("냉동실", tab_key="frozen")
    st.subheader("➕ 추가하기")
    render_add_form("냉동실")

with tab_all:
    st.subheader("전체보기")
    render_summary()
    st.divider()
    render_inventory(tab_key="all")

with tab_csv:
    st.subheader("CSV 파일로 한꺼번에 불러오기")

    with st.expander("CSV 형식 안내 (클릭해서 펼치기)"):
        st.markdown("""
**필요한 열: 물건이름 / 수량 / 유통기한 / 대분류 / 중분류**
- 유통기한 형식: `YYYY-MM-DD`
- 대분류: `미용` / `팬트리` / `냉장고` / `냉동실`
""")
        sample_df = pd.DataFrame({
            "물건이름": ["토너","굵은소금","삼겹살 구이용"],
            "수량": [1, 2, 5],
            "유통기한": ["2026-01-01","",""],
            "대분류": ["미용","팬트리","냉동실"],
            "중분류": ["스킨케어","양념류","육류"],
        })
        st.dataframe(sample_df, use_container_width=True)
        sample_csv = sample_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("⬇️ 샘플 CSV 다운로드", data=sample_csv,
                           file_name="재고_샘플.csv", mime="text/csv")

    uploaded_file = st.file_uploader("CSV 파일 선택", type=["csv"])
    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file, encoding="utf-8-sig")
            df_upload.columns = df_upload.columns.str.strip()

            required_cols = {"물건이름", "수량", "유통기한", "대분류"}
            if not required_cols.issubset(set(df_upload.columns)):
                st.error(f"❌ 필요한 열이 없어요! 현재 열: {list(df_upload.columns)}")
            else:
                st.dataframe(df_upload, use_container_width=True)
                mode = st.radio("불러오기 방식", ["기존 목록에 추가", "기존 목록 대체"], index=0)
                if st.button("✅ 불러오기", use_container_width=True):
                    if mode == "기존 목록 대체":
                        st.session_state.inventory = []

                    count, skipped = 0, 0
                    for _, row in df_upload.iterrows():
                        raw_name = row["물건이름"]
                        if pd.isna(raw_name) or str(raw_name).strip() == "":
                            continue

                        name = str(raw_name).strip()

                        raw_qty = row["수량"]
                        qty = 1 if pd.isna(raw_qty) or str(raw_qty).strip() == "" else int(float(str(raw_qty).strip()))

                        raw_cat = row["대분류"]
                        if pd.isna(raw_cat):
                            skipped += 1; continue
                        category = str(raw_cat).strip()
                        if category not in CATEGORY_NAMES:
                            skipped += 1; continue

                        raw_exp = row["유통기한"]
                        if pd.isna(raw_exp) or str(raw_exp).strip() == "":
                            exp = None
                        else:
                            try:
                                exp = pd.to_datetime(str(raw_exp).strip()).date()
                            except Exception:
                                exp = None

                        # 중분류: 있으면 사용, 없으면 기타
                        raw_sub = row.get("중분류", None)
                        if raw_sub is None or pd.isna(raw_sub) or str(raw_sub).strip() == "":
                            subcategory = "기타"
                        else:
                            subcategory = str(raw_sub).strip()
                            add_sub(category, subcategory)

                        existing = next(
                            (i for i, x in enumerate(st.session_state.inventory)
                             if x["name"] == name and x["category"] == category), None
                        )
                        if existing is not None:
                            st.session_state.inventory[existing]["qty"] += qty
                        else:
                            st.session_state.inventory.append({
                                "name": name, "qty": qty, "exp": exp,
                                "category": category, "subcategory": subcategory
                            })
                        count += 1

                    st.success(f"✅ {count}개 품목을 불러왔어요!" + (f" ({skipped}개 건너뜀)" if skipped else ""))
                    st.rerun()

        except Exception as e:
            st.error(f"파일을 읽는 중 오류가 발생했어요: {e}")

    if st.session_state.inventory:
        st.divider()
        df_export = pd.DataFrame([
            {"물건이름": x["name"], "수량": x["qty"], "유통기한": x["exp"] if x["exp"] is not None else "",
             "대분류": x["category"], "중분류": x.get("subcategory","기타")}
            for x in st.session_state.inventory
        ])
        csv_out = df_export.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("📥 전체 재고 CSV 저장", data=csv_out,
                           file_name="우리집_재고.csv", mime="text/csv")
