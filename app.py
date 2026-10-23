
from pathlib import Path
import streamlit as st
import pandas as pd
from motor_logic import load_archive, ball_screw_calc, belt_calc, evaluate_candidates

st.set_page_config(
    page_title="SEJUMOTION Motor Selection Dashboard V0.1",
    page_icon="⚙️",
    layout="wide"
)

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "data" / "SEJUMOTION_Motor_Specification_Archive_Integrated_67models.xlsx"

@st.cache_data
def get_archive():
    return load_archive(DATA_FILE)

archive = get_archive()

st.title("⚙️ Motor Selection Dashboard V0.1")
st.caption("Engineering Rule 기반 설계지원 Prototype · 현재 67개 Motor Specification Archive 연계")

st.warning(
    "이 Prototype은 **최종 모터 선정/설계 승인 도구가 아닙니다.** "
    "현재 Archive에는 정격토크·최대토크·Torque-Speed Curve·최대/허용 회전속도 정보가 충분하지 않아, "
    "Holding Torque와 Rotor Inertia를 이용한 **1차 후보 Screening**까지만 수행합니다. "
    "최종 선정은 세주모션 기술담당자의 검증이 필요합니다."
)

with st.sidebar:
    st.header("1. 설계조건")
    mechanism = st.radio("기구 방식", ["Ball Screw", "Belt"], horizontal=False)

    st.subheader("공통 운전조건")
    work_mass = st.number_input("워크 중량 (kg)", min_value=0.01, value=10.0 if mechanism=="Ball Screw" else 2.0, step=0.1)
    distance = st.number_input("이동거리 (m)", min_value=0.001, value=0.3 if mechanism=="Ball Screw" else 1.0, step=0.01)
    ta = st.number_input("가속시간 ta (s)", min_value=0.001, value=0.1, step=0.01)
    tb = st.number_input("정속시간 tb (s)", min_value=0.0, value=0.8, step=0.01)
    td = st.number_input("감속시간 td (s)", min_value=0.001, value=0.1, step=0.01)
    cycle = st.number_input("사이클시간 tc (s)", min_value=0.001, value=2.0, step=0.1)
    eta = st.number_input("기계효율 η", min_value=0.01, max_value=1.0, value=0.9 if mechanism=="Ball Screw" else 0.8, step=0.01)
    mu = st.number_input("마찰계수 μ", min_value=0.0, value=0.1, step=0.01)
    external_force = st.number_input("외력 F (N)", min_value=0.0, value=0.0, step=1.0)
    coupling_j = st.number_input("커플링 관성 Jc (kg·m²)", min_value=0.0, value=0.00001 if mechanism=="Ball Screw" else 0.0, format="%.8f")

    if mechanism == "Ball Screw":
        st.subheader("Ball Screw 조건")
        screw_length = st.number_input("볼스크루 길이 (m)", min_value=0.01, value=0.5, step=0.05)
        screw_diameter = st.number_input("볼스크루 직경 (m)", min_value=0.001, value=0.02, step=0.001, format="%.3f")
        screw_lead = st.number_input("볼스크루 리드 (m/rev)", min_value=0.001, value=0.02, step=0.001, format="%.3f")
        density = st.number_input("재료 밀도 (kg/m³)", min_value=100.0, value=7850.0, step=50.0)
    else:
        st.subheader("Belt 조건")
        pulley_d = st.number_input("풀리 직경 (m)", min_value=0.001, value=0.05, step=0.005, format="%.3f")
        pulley_mass = st.number_input("풀리 무게 (kg)", min_value=0.0, value=0.5, step=0.1)

    st.divider()
    st.header("2. 1차 Screening 기준")
    safety_factor = st.slider("Holding Torque 임시 안전계수", 1.0, 3.0, 1.5, 0.1,
        help="동적토크 자료가 없으므로 임시 1차 Screening에만 사용합니다.")
    inertia_limit = st.selectbox("허용 관성비(임시)", [10.0, 20.0, 30.0, 50.0], index=1,
        help="실제 허용 관성비는 제조사/드라이버 조건에 따라 달라질 수 있습니다.")
    exclude_qa = st.checkbox("QA 확인필요 모델 기본 제외", value=True)

    use_frame = st.checkbox("최대 Frame Size 제한")
    max_frame = st.number_input("최대 Frame Size (mm)", min_value=10.0, value=60.0, step=1.0, disabled=not use_frame)
    use_length = st.checkbox("최대 Motor Length 제한")
    max_length = st.number_input("최대 Motor Length (mm)", min_value=10.0, value=100.0, step=1.0, disabled=not use_length)
    use_current = st.checkbox("최대 Rated Current 제한")
    max_current = st.number_input("최대 Rated Current (A)", min_value=0.1, value=4.0, step=0.1, disabled=not use_current)

motion_time = ta + tb + td
if cycle < motion_time:
    st.error(f"사이클시간 tc({cycle:.3f}s)는 운전시간 ta+tb+td({motion_time:.3f}s) 이상이어야 합니다.")
    st.stop()

try:
    if mechanism == "Ball Screw":
        calc = ball_screw_calc(
            work_mass, distance, ta, tb, td, cycle, eta, mu, external_force,
            screw_length, screw_diameter, screw_lead, coupling_j, density
        )
    else:
        calc = belt_calc(
            work_mass, distance, ta, tb, td, cycle, eta, mu, external_force,
            pulley_d, pulley_mass, coupling_j
        )
except ValueError as e:
    st.error(str(e))
    st.stop()

evaluated = evaluate_candidates(
    archive=archive,
    calc=calc,
    ta=ta, tb=tb, td=td,
    safety_factor=safety_factor,
    inertia_ratio_limit=inertia_limit,
    max_frame_mm=max_frame if use_frame else None,
    max_length_mm=max_length if use_length else None,
    max_current_a=max_current if use_current else None,
    exclude_qa_risk=exclude_qa,
)

tabs = st.tabs(["📐 계산결과", "✅ 1차 후보", "🗂 Motor Archive", "⚠️ 한계·검증사항"])

with tabs[0]:
    st.subheader("Engineering Calculation")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("최고 선속도 Vmax", f"{calc.vmax_mps:.3f} m/s")
    c2.metric("필요 회전속도", f"{calc.rpm:,.0f} rpm")
    c3.metric("부하 관성 JL", f"{calc.load_inertia_kgm2:.3e} kg·m²")
    c4.metric("주행토크 Tf", f"{calc.running_torque_nm:.3f} N·m")

    st.markdown("#### 계산 흐름")
    st.info(
        f"**{mechanism}** → Vmax 계산 → 필요 rpm 계산 → 부하관성 JL 계산 → "
        "각 모터의 Rotor Inertia를 대입해 가속/감속토크·RMS토크·관성비 계산 → "
        "Motor Archive와 1차 비교"
    )

    # Show a representative candidate-dependent torque using best passing model if available
    passed = evaluated[evaluated["1차 후보"]=="PASS"]
    reference = passed.iloc[0] if len(passed) else evaluated.iloc[0]
    st.markdown("#### 대표 후보를 대입한 토크 계산 예")
    r1,r2,r3,r4 = st.columns(4)
    r1.metric("예시 모델", str(reference["파일명 모델"]))
    r2.metric("가속토크 Ta", f'{reference["Acceleration Torque (N·m)"]:.3f} N·m')
    r3.metric("감속토크 Td", f'{reference["Deceleration Torque (N·m)"]:.3f} N·m')
    r4.metric("실효토크 RMS", f'{reference["RMS Torque (N·m)"]:.3f} N·m')

with tabs[1]:
    st.subheader("67개 Archive 기반 1차 후보 Screening")
    passed = evaluated[evaluated["1차 후보"]=="PASS"].copy()

    if len(passed) == 0:
        st.error("현재 임시 Screening 기준을 모두 만족하는 후보가 없습니다.")
        st.caption("안전계수·관성비·크기/전류 제한을 조정하거나, 추가 모터 사양을 확보해 검토하십시오.")
    else:
        st.success(f"현재 조건에서 **{len(passed)}개** 모델이 1차 후보로 검색되었습니다.")
        topn = passed.head(10).copy()
        show_cols = [
            "파일명 모델","Frame Size (mm)","Motor Length (mm)","Rated Current (A)",
            "Holding Torque (N·m)","Rotor Inertia (g·cm²)","Inertia Ratio",
            "Acceleration Torque (N·m)","RMS Torque (N·m)","Holding Torque Margin",
            "동적 토크 검증","속도 검증"
        ]
        st.dataframe(
            topn[show_cols].style.format({
                "Holding Torque (N·m)":"{:.3f}",
                "Inertia Ratio":"{:.1f}",
                "Acceleration Torque (N·m)":"{:.3f}",
                "RMS Torque (N·m)":"{:.3f}",
                "Holding Torque Margin":"{:.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("#### 후보 해석")
        best = topn.iloc[0]
        st.write(
            f"**1차 후보 예시: {best['파일명 모델']}** — "
            f"Holding Torque {best['Holding Torque (N·m)']:.3f} N·m, "
            f"관성비 {best['Inertia Ratio']:.1f}, "
            f"가속토크 계산값 {best['Acceleration Torque (N·m)']:.3f} N·m."
        )
        st.warning(
            "여기서 PASS는 **최종 적합 판정이 아닙니다.** "
            "해당 rpm에서의 실제 가용토크(Torque-Speed Curve), 정격/최대토크, "
            "드라이버 조합을 확인한 뒤 최종 판단해야 합니다."
        )

        csv = topn[show_cols].to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ 상위 후보 CSV 저장",
            data=csv,
            file_name="motor_selection_candidates.csv",
            mime="text/csv"
        )

    with st.expander("검토/제외 모델도 보기"):
        reject = evaluated[evaluated["1차 후보"]!="PASS"].copy()
        st.dataframe(
            reject[[
                "파일명 모델","Holding Torque (N·m)","Rotor Inertia (g·cm²)",
                "Inertia Ratio","QA_Risk","QA / 확인사항"
            ]].head(30),
            use_container_width=True,
            hide_index=True,
        )

with tabs[2]:
    st.subheader("Motor Specification Archive")
    q = st.text_input("모델명 검색", "")
    view = archive.copy()
    if q.strip():
        view = view[view["파일명 모델"].astype(str).str.contains(q.strip(), case=False, na=False)]

    a1,a2,a3 = st.columns(3)
    a1.metric("현재 Archive", f"{len(archive)} models")
    a2.metric("Frame Size 범위", f"{archive['Frame Size (mm)'].min():.0f}–{archive['Frame Size (mm)'].max():.0f} mm")
    a3.metric("QA 확인필요", f"{archive['QA_Risk'].sum()} models")

    cols = [
        "파일명 모델","모터 유형","Step Angle (deg)","Frame Size (mm)","Motor Length (mm)",
        "Rated Current (A)","Holding Torque (N·m)","Resistance (ohm)",
        "Inductance (mH)","Rotor Inertia (g·cm²)","Motor Weight (kg)",
        "QA / 확인사항"
    ]
    st.dataframe(view[cols], use_container_width=True, hide_index=True)

    st.caption("※ 첨부 목록 기준 57SJM4972-21B 모델은 현재 67개 Archive에 아직 미반영 상태입니다.")

with tabs[3]:
    st.subheader("현재 V0.1에서 가능한 것")
    st.markdown(
        """
        - Ball Screw / Belt 설계조건 입력
        - 최고속도, 필요 rpm, 부하관성, 주행토크 자동 계산
        - 각 모터 Rotor Inertia를 반영한 가속/감속토크·RMS토크·관성비 계산
        - Frame / Length / Current / Holding Torque 기반 1차 후보 Screening
        - QA 확인필요 모델 기본 제외
        """
    )

    st.subheader("최종 선정 전에 반드시 추가해야 할 데이터")
    st.markdown(
        """
        1. **Torque-Speed Curve** — 해당 rpm에서 실제 사용 가능한 토크
        2. **Rated Torque / Maximum Torque**
        3. **최대·허용 회전속도**
        4. **Driver Matching / 전원조건**
        5. 제조사별 **허용 관성비 기준**
        6. 필요한 경우 Shaft / Mount 상세 치수
        """
    )

    st.error(
        "Holding Torque는 정지 상태의 유지토크이며, 운전 중 토크를 그대로 의미하지 않습니다. "
        "따라서 본 V0.1의 추천 결과를 실제 장비 설계에 바로 사용해서는 안 됩니다."
    )
