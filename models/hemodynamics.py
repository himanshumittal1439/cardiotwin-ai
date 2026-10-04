"""
CardioTwin Hemodynamics Engine
==============================
High-fidelity lumped-parameter biophysical cardiovascular simulation model
based on Suga-Sagawa time-varying elastance, 3-element Windkessel vascular impedance,
and dynamic valve fluid mechanics.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, List


@dataclass
class PatientHemodynamicState:
    hr: float           # Heart Rate (beats per minute)
    e_max: float        # LV Contractility (End-systolic elastance, mmHg/mL)
    e_min: float        # LV Baseline diastolic elastance (mmHg/mL)
    v0: float           # LV Unstressed volume (mL)
    r_sys: float        # Systemic Vascular Resistance (mmHg * s / mL)
    c_art: float        # Arterial Compliance (mL / mmHg)
    r_ao: float         # Aortic valve resistance (mmHg * s / mL)
    r_mi: float         # Mitral valve resistance (mmHg * s / mL)
    v_total: float      # Circulating venous preload reference (mL)


def normalized_elastance(t_normalized: float) -> float:
    """
    Normalized double-Hill cardiac activation function e_n(t_n)
    representing ventricular muscular activation during cardiac cycle.
    """
    tn = t_normalized % 1.0
    # Normalized time parameters from canonical human physiology
    n1, n2 = 1.32, 21.9
    c1, c2 = 0.70, 1.17
    term1 = (tn / c1) ** n1 / (1.0 + (tn / c1) ** n1)
    term2 = 1.0 / (1.0 + (tn / c2) ** n2)
    return float(1.55 * term1 * term2)


class CardiacDigitalTwinEngine:
    """
    Biophysical numerical solver for left-ventricular and systemic arterial
    pressures, volumes, and flows over one or more cardiac cycles.
    """

    def __init__(self, state: PatientHemodynamicState):
        self.state = state

    def simulate_cardiac_cycle(self, cycles: int = 3, dt: float = 0.002) -> Dict[str, np.ndarray]:
        """
        Simulates the cardiac cycle using Runge-Kutta / Forward Euler numerical integration.
        Returns time-series arrays for time, LV pressure, aortic pressure, LA pressure,
        LV volume, and aortic flow.
        """
        hr = max(30.0, min(220.0, self.state.hr))
        t_cycle = 60.0 / hr  # Duration of single beat in seconds
        t_systole = 0.3 * np.sqrt(t_cycle)  # Bazett-like scaling for systole duration
        total_time = cycles * t_cycle
        time_steps = int(total_time / dt)

        # Time array
        t = np.linspace(0, total_time, time_steps)

        # State variable arrays
        p_lv = np.zeros(time_steps)
        v_lv = np.zeros(time_steps)
        p_ao = np.zeros(time_steps)
        q_ao = np.zeros(time_steps)
        q_mi = np.zeros(time_steps)
        e_t = np.zeros(time_steps)

        # Initial conditions
        v_lv_curr = 135.0  # End-diastolic volume baseline (mL)
        p_ao_curr = 80.0   # Diastolic aortic pressure (mmHg)
        p_la_curr = 10.0   # Left atrial pressure baseline (mmHg)

        e_min = self.state.e_min
        e_max = self.state.e_max
        v0 = self.state.v0
        r_sys = self.state.r_sys
        c_art = self.state.c_art
        r_ao = self.state.r_ao
        r_mi = self.state.r_mi

        for i, curr_t in enumerate(t):
            # Time within the beat
            beat_t = curr_t % t_cycle
            # Normalized elastance activation
            en = normalized_elastance(beat_t / t_systole if beat_t < t_systole * 1.5 else 1.2)
            e_curr = e_min + (e_max - e_min) * en
            e_t[i] = e_curr

            # Instantaneous LV pressure from elastance
            p_lv_curr = max(2.0, e_curr * (v_lv_curr - v0))

            # Valve Mechanics (Diode Flow Laws)
            # Aortic Valve: Opens if P_lv > P_ao
            if p_lv_curr > p_ao_curr:
                flow_ao = (p_lv_curr - p_ao_curr) / r_ao
            else:
                flow_ao = 0.0

            # Mitral Valve: Opens if P_la > P_lv
            if p_la_curr > p_lv_curr:
                flow_mi = (p_la_curr - p_lv_curr) / r_mi
            else:
                flow_mi = 0.0

            # 3-Element Windkessel Systemic Arterial ODE:
            # dP_ao/dt = (flow_ao - p_ao / r_sys) / c_art
            dp_ao = (flow_ao - (p_ao_curr / r_sys)) / c_art
            p_ao_curr += dp_ao * dt

            # Ventricular Volume Conservation:
            # dV_lv/dt = flow_mi - flow_ao
            dv_lv = flow_mi - flow_ao
            v_lv_curr += dv_lv * dt

            # Record state
            p_lv[i] = p_lv_curr
            v_lv[i] = v_lv_curr
            p_ao[i] = p_ao_curr
            q_ao[i] = flow_ao
            q_mi[i] = flow_mi

        # Extract stable final cycle for metrics and clinical loop plotting
        samples_per_cycle = int(t_cycle / dt)
        last_cycle_start = max(0, time_steps - samples_per_cycle)

        final_t = t[last_cycle_start:] - t[last_cycle_start]
        final_p_lv = p_lv[last_cycle_start:]
        final_v_lv = v_lv[last_cycle_start:]
        final_p_ao = p_ao[last_cycle_start:]
        final_q_ao = q_ao[last_cycle_start:]
        final_q_mi = q_mi[last_cycle_start:]

        return {
            "all_time": t,
            "all_p_lv": p_lv,
            "all_p_ao": p_ao,
            "all_v_lv": v_lv,
            "cycle_time": final_t,
            "cycle_p_lv": final_p_lv,
            "cycle_p_ao": final_p_ao,
            "cycle_v_lv": final_v_lv,
            "cycle_q_ao": final_q_ao,
            "cycle_q_mi": final_q_mi,
            "elastance": e_t[last_cycle_start:],
        }

    def compute_clinical_biomarkers(self, sim_data: Dict[str, np.ndarray], bsa: float = 1.9) -> Dict[str, float]:
        """
        Computes clinical hemodynamic endpoints:
        - Stroke Volume (SV)
        - Ejection Fraction (LVEF %)
        - Cardiac Output (CO L/min)
        - Cardiac Index (CI L/min/m2)
        - Systolic & Diastolic BP (SBP, DBP mmHg)
        - Mean Arterial Pressure (MAP mmHg)
        - Stroke Work (SW mmHg*mL)
        - Pressure-Volume Area (PVA proxy for MVO2 myocardial oxygen consumption)
        """
        v_cycle = sim_data["cycle_v_lv"]
        p_lv_cycle = sim_data["cycle_p_lv"]
        p_ao_cycle = sim_data["cycle_p_ao"]

        edv = float(np.max(v_cycle))
        esv = float(np.min(v_cycle))
        sv = max(5.0, edv - esv)
        ef = (sv / edv) * 100.0 if edv > 0 else 50.0

        hr = self.state.hr
        co = (sv * hr) / 1000.0  # L/min
        ci = co / bsa            # L/min/m2

        sbp = float(np.max(p_ao_cycle))
        dbp = float(np.min(p_ao_cycle))
        map_val = dbp + (1.0 / 3.0) * (sbp - dbp)

        # Numerical integration of PV Loop area: Stroke Work = int(P_lv dV)
        # Approximate loop polygon area via Green's theorem / trapezoidal
        dv = np.diff(v_cycle, append=v_cycle[0])
        stroke_work = float(np.abs(np.sum(p_lv_cycle * dv)))
        
        # PVA (Pressure Volume Area) = Stroke Work + Potential Energy
        potential_energy = 0.5 * p_lv_cycle[np.argmin(v_cycle)] * (esv - self.state.v0)
        pva = stroke_work + max(0.0, potential_energy)
        mvo2 = 1.8e-4 * pva + 1.2  # Canonical conversion to mL O2 / 100g LV mass

        return {
            "EDV": round(edv, 1),
            "ESV": round(esv, 1),
            "SV": round(sv, 1),
            "LVEF": round(ef, 1),
            "CO": round(co, 2),
            "CI": round(ci, 2),
            "SBP": round(sbp, 1),
            "DBP": round(dbp, 1),
            "MAP": round(map_val, 1),
            "StrokeWork": round(stroke_work, 1),
            "MVO2": round(mvo2, 2),
            "SVR": round(self.state.r_sys * 80.0, 1), # converted to dyn*s/cm5 standard units
        }


def apply_pharmacological_intervention(
    base_state: PatientHemodynamicState,
    beta_blocker_dose: float = 0.0,  # 0 to 100% titration
    ace_inhibitor_dose: float = 0.0, # 0 to 100% titration
    inotrope_dose: float = 0.0,      # 0 to 100% titration (Dobutamine / Milrinone)
    vasopressor_dose: float = 0.0,   # 0 to 100% titration (Norepinephrine)
    diuretic_dose: float = 0.0,      # 0 to 100% titration (Furosemide)
    exercise_intensity: float = 0.0  # 0 to 100% aerobic stress
) -> PatientHemodynamicState:
    """
    Simulates in-silico pharmacodynamics and autonomic nervous system stress response
    on the digital twin's biophysical state parameters.
    """
    # Clone state
    hr = base_state.hr
    e_max = base_state.e_max
    e_min = base_state.e_min
    v0 = base_state.v0
    r_sys = base_state.r_sys
    c_art = base_state.c_art
    r_ao = base_state.r_ao
    r_mi = base_state.r_mi
    v_total = base_state.v_total

    # 1. Beta-Blocker effect: Chronotropic & Inotropic reduction, modest SVR reduction
    if beta_blocker_dose > 0:
        factor = beta_blocker_dose / 100.0
        hr -= 25.0 * factor
        e_max *= (1.0 - 0.20 * factor)
        r_sys *= (1.0 - 0.10 * factor)

    # 2. ACE Inhibitor / ARB: Vasodilation, afterload reduction, improves compliance
    if ace_inhibitor_dose > 0:
        factor = ace_inhibitor_dose / 100.0
        r_sys *= (1.0 - 0.32 * factor)
        c_art *= (1.0 + 0.25 * factor)

    # 3. Inotrope (Dobutamine / Milrinone): Contractility boost, slight tachycardia
    if inotrope_dose > 0:
        factor = inotrope_dose / 100.0
        e_max *= (1.0 + 0.85 * factor)
        hr += 15.0 * factor
        r_sys *= (1.0 - 0.15 * factor)

    # 4. Vasopressor (Norepinephrine): Potent peripheral vasoconstriction, modest contractility
    if vasopressor_dose > 0:
        factor = vasopressor_dose / 100.0
        r_sys *= (1.0 + 0.70 * factor)
        e_max *= (1.0 + 0.25 * factor)
        c_art *= (1.0 - 0.20 * factor)

    # 5. Diuretic (Furosemide): Venous preload reduction
    if diuretic_dose > 0:
        factor = diuretic_dose / 100.0
        v_total *= (1.0 - 0.25 * factor)
        v0 += 5.0 * factor

    # 6. Aerobic Exercise: Sympathetic drive (HR up, Emax up, SVR down via metabolic hyperemia)
    if exercise_intensity > 0:
        factor = exercise_intensity / 100.0
        hr += 65.0 * factor
        e_max *= (1.0 + 0.60 * factor)
        r_sys *= (1.0 - 0.40 * factor)
        c_art *= (1.0 - 0.10 * factor)

    # Boundaries
    hr = max(38.0, min(195.0, hr))
    e_max = max(0.4, min(4.8, e_max))
    r_sys = max(0.3, min(2.5, r_sys))
    c_art = max(0.4, min(2.5, c_art))

    return PatientHemodynamicState(
        hr=hr,
        e_max=e_max,
        e_min=e_min,
        v0=v0,
        r_sys=r_sys,
        c_art=c_art,
        r_ao=r_ao,
        r_mi=r_mi,
        v_total=v_total
    )
