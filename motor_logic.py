
from __future__ import annotations
import math
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import numpy as np

G = 9.8  # m/s^2

RISK_WORDS = [
    "단위 재확인", "확인 필요", "불일치", "원본 재확인",
    "재확인 권장", "오기", "정식 사양", "제조사 확인"
]

@dataclass
class CalcResult:
    mechanism: str
    vmax_mps: float
    rpm: float
    load_inertia_kgm2: float
    running_torque_nm: float
    omega_rad_s: float
    motion_time_s: float
    cycle_time_s: float

def load_archive(path: str | Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Motor_Master", header=1)
    # remove fully empty rows and coerce core numeric columns
    df = df.dropna(how="all").copy()
    numeric_cols = [
        "Step Angle (deg)", "Frame Size (mm)", "Motor Length (mm)",
        "Rated Current (A)", "Holding Torque (mN·m)", "Holding Torque (N·m)",
        "Resistance (ohm)", "Inductance (mH)", "Rotor Inertia (g·cm²)",
        "Motor Weight (kg)"
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "Holding Torque (N·m)" not in df.columns and "Holding Torque (mN·m)" in df.columns:
        df["Holding Torque (N·m)"] = df["Holding Torque (mN·m)"] / 1000.0

    if "QA / 확인사항" not in df.columns:
        df["QA / 확인사항"] = ""
    df["QA / 확인사항"] = df["QA / 확인사항"].fillna("").astype(str)
    df["QA_Risk"] = df["QA / 확인사항"].apply(
        lambda x: any(w in x for w in RISK_WORDS)
    )
    return df

def calc_vmax(distance_m: float, ta: float, tb: float, td: float) -> float:
    denom = 0.5 * ta + tb + 0.5 * td
    if denom <= 0:
        raise ValueError("가속·정속·감속 시간 조합이 올바르지 않습니다.")
    return distance_m / denom

def ball_screw_calc(
    work_mass_kg: float,
    distance_m: float,
    ta: float,
    tb: float,
    td: float,
    cycle_time_s: float,
    efficiency: float,
    friction_coeff: float,
    external_force_n: float,
    screw_length_m: float,
    screw_diameter_m: float,
    screw_lead_m: float,
    coupling_inertia_kgm2: float,
    material_density_kgm3: float = 7850.0,
) -> CalcResult:
    if screw_lead_m <= 0 or efficiency <= 0:
        raise ValueError("볼스크루 리드와 효율은 0보다 커야 합니다.")
    vmax = calc_vmax(distance_m, ta, tb, td)
    rev_s = vmax / screw_lead_m
    rpm = rev_s * 60.0
    omega = 2.0 * math.pi * rev_s

    screw_mass = material_density_kgm3 * math.pi * (screw_diameter_m / 2.0) ** 2 * screw_length_m
    jl = (
        coupling_inertia_kgm2
        + (1.0 / 8.0) * screw_mass * screw_diameter_m ** 2
        + work_mass_kg * screw_lead_m ** 2 / (4.0 * math.pi ** 2)
    )
    tf = screw_lead_m / (2.0 * math.pi * efficiency) * (
        friction_coeff * G * work_mass_kg + external_force_n
    )
    return CalcResult(
        mechanism="Ball Screw",
        vmax_mps=vmax,
        rpm=rpm,
        load_inertia_kgm2=jl,
        running_torque_nm=tf,
        omega_rad_s=omega,
        motion_time_s=ta + tb + td,
        cycle_time_s=cycle_time_s,
    )

def belt_calc(
    work_mass_kg: float,
    distance_m: float,
    ta: float,
    tb: float,
    td: float,
    cycle_time_s: float,
    efficiency: float,
    friction_coeff: float,
    external_force_n: float,
    pulley_diameter_m: float,
    pulley_mass_kg: float,
    coupling_inertia_kgm2: float,
) -> CalcResult:
    if pulley_diameter_m <= 0 or efficiency <= 0:
        raise ValueError("풀리 직경과 효율은 0보다 커야 합니다.")
    vmax = calc_vmax(distance_m, ta, tb, td)
    rev_s = vmax / (math.pi * pulley_diameter_m)
    rpm = rev_s * 60.0
    omega = 2.0 * math.pi * rev_s

    jl = (
        coupling_inertia_kgm2
        + 0.25 * work_mass_kg * pulley_diameter_m ** 2
        + (1.0 / 8.0) * pulley_mass_kg * pulley_diameter_m ** 2 * 2.0
    )
    tf = pulley_diameter_m / (2.0 * efficiency) * (
        friction_coeff * G * work_mass_kg + external_force_n
    )
    return CalcResult(
        mechanism="Belt",
        vmax_mps=vmax,
        rpm=rpm,
        load_inertia_kgm2=jl,
        running_torque_nm=tf,
        omega_rad_s=omega,
        motion_time_s=ta + tb + td,
        cycle_time_s=cycle_time_s,
    )

def evaluate_candidates(
    archive: pd.DataFrame,
    calc: CalcResult,
    ta: float,
    tb: float,
    td: float,
    safety_factor: float = 1.5,
    inertia_ratio_limit: float = 20.0,
    max_frame_mm: float | None = None,
    max_length_mm: float | None = None,
    max_current_a: float | None = None,
    exclude_qa_risk: bool = True,
) -> pd.DataFrame:
    df = archive.copy()

    # Unit conversion: 1 g·cm² = 1e-7 kg·m²
    df["Rotor Inertia (kg·m²)"] = df["Rotor Inertia (g·cm²)"] * 1e-7
    df["Inertia Ratio"] = calc.load_inertia_kgm2 / df["Rotor Inertia (kg·m²)"]

    # Candidate-dependent acceleration/deceleration torque
    df["Acceleration Torque (N·m)"] = (
        (calc.load_inertia_kgm2 + df["Rotor Inertia (kg·m²)"])
        * calc.omega_rad_s / ta
        + calc.running_torque_nm
    )
    df["Deceleration Torque (N·m)"] = (
        (calc.load_inertia_kgm2 + df["Rotor Inertia (kg·m²)"])
        * calc.omega_rad_s / td
        - calc.running_torque_nm
    ).abs()

    df["RMS Torque (N·m)"] = np.sqrt(
        (
            df["Acceleration Torque (N·m)"] ** 2 * ta
            + calc.running_torque_nm ** 2 * tb
            + df["Deceleration Torque (N·m)"] ** 2 * td
        )
        / calc.cycle_time_s
    )
    df["Required Peak × SF (N·m)"] = df["Acceleration Torque (N·m)"] * safety_factor
    df["Holding Torque Margin"] = (
        df["Holding Torque (N·m)"] / df["Required Peak × SF (N·m)"]
    )

    # Provisional screen only — holding torque is NOT dynamic torque.
    conditions = pd.Series(True, index=df.index)
    conditions &= df["Holding Torque (N·m)"].notna()
    conditions &= df["Rotor Inertia (kg·m²)"].notna()
    conditions &= df["Holding Torque (N·m)"] >= df["Required Peak × SF (N·m)"]
    conditions &= df["Inertia Ratio"] <= inertia_ratio_limit

    if max_frame_mm is not None:
        conditions &= df["Frame Size (mm)"] <= max_frame_mm
    if max_length_mm is not None:
        conditions &= df["Motor Length (mm)"] <= max_length_mm
    if max_current_a is not None:
        conditions &= df["Rated Current (A)"] <= max_current_a
    if exclude_qa_risk:
        conditions &= ~df["QA_Risk"]

    df["1차 후보"] = np.where(conditions, "PASS", "검토/제외")
    df["동적 토크 검증"] = "Torque-Speed Curve 필요"
    df["속도 검증"] = "최대/허용 rpm 필요"

    # Sort passing models first, then minimize oversizing and inertia ratio.
    df["_pass_rank"] = np.where(df["1차 후보"].eq("PASS"), 0, 1)
    df["_oversize"] = np.where(
        df["Holding Torque Margin"].notna(),
        (df["Holding Torque Margin"] - 1.0).abs(),
        9999
    )
    df = df.sort_values(
        by=["_pass_rank", "_oversize", "Inertia Ratio", "Rated Current (A)"],
        ascending=[True, True, True, True],
        na_position="last"
    ).drop(columns=["_pass_rank", "_oversize"])

    return df
