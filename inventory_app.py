import streamlit as st
import pandas as pd
from datetime import date, timedelta

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(page_title="🏠 우리집 재고 관리", layout="centered")

st.title("🏠 우리집 재고 관리")
st.caption("물건을 추가하고, 수량을 관리하고, 유통기한을 체크하세요!")

# ── 세션 상태 초기화 (데이터를 앱이 켜져 있는 동안 유지) ──────
if "inventory" not in st.session_state:
    st.session_state.inventory = []   # 빈 목록으로 시작

# ══════════════════════════════════════════════════════════════
# 1. 물건 추가 폼
# ══════════════════════════════════════════════════════════════
st.subheader("➕ 물건 추가하기")

with st.form("add_item_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        item_name = st.text_input("물건 이름", placeholder="예) 두부, 우유, 샴푸")
    with col2:
        item_qty = st.number_input("수량", min_value=1, max_value=999, value=1)
    with col3:
        # 기본값: 오늘로부터 30일 뒤
        item_exp = st.date_input("유통기한", value=date.today() + timedelta(days=30))

    submitted = st.form_submit_button("추가하기", use_container_width=True)

    if submitted:
        if item_name.strip() == "":
            st.error("물건 이름을 입력해 주세요!")
        else:
            # 이미 있는 물건이면 수량만 더하기
            existing = next(
                (i for i, x in enumerate(st.session_state.inventory)
                 if x["name"] == item_name.strip()),
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
# 2. 재고 현황 테이블
# ══════════════════════════════════════════════════════════════
st.subheader("📦 현재 재고 현황")

if len(st.session_state.inventory) == 0:
    st.info("아직 물건이 없어요. 위에서 물건을 추가해 보세요! 😊")
else:
    today = date.today()
    warning_days = 7   # 7일 이내면 유통기한 주의

    for idx, item in enumerate(st.session_state.inventory):
        days_left = (item["exp"] - today).days

        # ── 상태 뱃지 결정 ──────────────────────────────────────
        badges = []

        # 수량 경고
        if item["qty"] <= 0:
            badges.append("🔴 재고 없음")
        elif item["qty"] <= 2:
            badges.append("🛒 구매 필요")

        # 유통기한 경고
        if days_left < 0:
            badges.append("⛔ 유통기한 만료")
        elif days_left <= warning_days:
            badges.append(f"⚠️ 주의 (D-{days_left})")
        else:
            badges.append(f"✅ D-{days_left}")

        badge_str = "  ".join(badges)

        # ── 한 행 렌더링 ─────────────────────────────────────────
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

    # ── 요약 통계 ─────────────────────────────────────────────
    total_items = len(st.session_state.inventory)
    need_buy = sum(1 for x in st.session_state.inventory if x["qty"] <= 2)
    exp_warn = sum(
        1 for x in st.session_state.inventory
        if 0 <= (x["exp"] - today).days <= warning_days
    )

    st.subheader("📊 요약")
    c1, c2, c3 = st.columns(3)
    c1.metric("전체 품목 수", f"{total_items}개")
    c2.metric("구매 필요 품목", f"{need_buy}개")
    c3.metric("유통기한 주의", f"{exp_warn}개")

# ══════════════════════════════════════════════════════════════
# 3. CSV 내보내기 (보너스 기능)
# ══════════════════════════════════════════════════════════════
if st.session_state.inventory:
    st.divider()
    df = pd.DataFrame(st.session_state.inventory)
    df.columns = ["물건 이름", "수량", "유통기한"]
    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 재고 목록 CSV로 저장",
        data=csv,
        file_name="우리집_재고.csv",
        mime="text/csv",
    )
