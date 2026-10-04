"""
CardioTwin Clinical Cohort Profiles
===================================
Pre-configured baseline patient cohorts reflecting diverse cardiovascular
pathologies and physiological phenotypes.
"""

from dataclasses import dataclass
from typing import Dict
from models.hemodynamics import PatientHemodynamicState


@dataclass
class PatientProfile:
    id: str
    name: str
    age: int
    gender: str
    clinical_history: str
    nyha_class: str
    bsa: float
    state: PatientHemodynamicState
    clinical_notes: str
    baseline_ecg_rhythm: str


PATIENT_COHORTS: Dict[str, PatientProfile] = {
    "athlete": PatientProfile(
        id="PT-101",
        name="Marcus Vance (Endurance Athlete)",
        age=28,
        gender="Male",
        clinical_history="Marathon runner, physiological bradycardia, athlete's heart adaptations.",
        nyha_class="Class I (None)",
        bsa=2.05,
        state=PatientHemodynamicState(
            hr=52.0,
            e_max=2.6,
            e_min=0.04,
            v0=12.0,
            r_sys=0.85,
            c_art=1.65,
            r_ao=0.01,
            r_mi=0.01,
            v_total=5200.0
        ),
        clinical_notes="Superb cardiovascular reserve, high stroke volume, low resting oxygen demand.",
        baseline_ecg_rhythm="Sinus Bradycardia (Normal Variant)"
    ),

    "hypertensive": PatientProfile(
        id="PT-204",
        name="Eleanor Chen (Stage 2 Hypertension)",
        age=59,
        gender="Female",
        clinical_history="Chronic essential hypertension, arterial stiffness, mild concentric LV hypertrophy.",
        nyha_class="Class I-II",
        bsa=1.75,
        state=PatientHemodynamicState(
            hr=78.0,
            e_max=2.1,
            e_min=0.09,
            v0=18.0,
            r_sys=1.45,
            c_art=0.72,
            r_ao=0.01,
            r_mi=0.01,
            v_total=4700.0
        ),
        clinical_notes="Significant afterload elevation. Risk of hypertensive emergency or diastolic dysfunction.",
        baseline_ecg_rhythm="Normal Sinus Rhythm with LVH Voltage Criteria"
    ),

    "hfref": PatientProfile(
        id="PT-309",
        name="Robert Davies (Decompensated HFrEF)",
        age=67,
        gender="Male",
        clinical_history="Ischemic cardiomyopathy, prior anterior STEMI, dilated LV, severe systolic impairment.",
        nyha_class="Class III (Moderate-Severe)",
        bsa=1.88,
        state=PatientHemodynamicState(
            hr=94.0,
            e_max=0.68,
            e_min=0.12,
            v0=38.0,
            r_sys=1.35,
            c_art=0.80,
            r_ao=0.01,
            r_mi=0.015,
            v_total=5600.0
        ),
        clinical_notes="LVEF ~28%. Highly fragile to volume overload; indicated for GDMT neurohormonal blockade.",
        baseline_ecg_rhythm="Sinus Tachycardia with Pathologic Q Waves"
    ),

    "aortic_stenosis": PatientProfile(
        id="PT-412",
        name="Arthur Pendelton (Severe Aortic Stenosis)",
        age=74,
        gender="Male",
        clinical_history="Calcific aortic valve stenosis, exertional dyspnea, elevated transvalvular gradient.",
        nyha_class="Class III",
        bsa=1.82,
        state=PatientHemodynamicState(
            hr=76.0,
            e_max=2.3,
            e_min=0.10,
            v0=20.0,
            r_sys=1.05,
            c_art=0.90,
            r_ao=0.075,  # High valve resistance gradient
            r_mi=0.01,
            v_total=4900.0
        ),
        clinical_notes="Marked transvalvular pressure gradient (>50 mmHg). High LV wall stress during ejection.",
        baseline_ecg_rhythm="Normal Sinus Rhythm with Strain Pattern"
    ),

    "cardiogenic_shock": PatientProfile(
        id="PT-520",
        name="Sarah Jenkins (Acute Cardiogenic Shock)",
        age=63,
        gender="Female",
        clinical_history="Acute extensive myocardial infarction, hypoperfusion, oliguria, cold extremities in CCU.",
        nyha_class="Class IV (Severe / Bedbound)",
        bsa=1.70,
        state=PatientHemodynamicState(
            hr=118.0,
            e_max=0.50,
            e_min=0.14,
            v0=42.0,
            r_sys=1.60,
            c_art=0.65,
            r_ao=0.01,
            r_mi=0.012,
            v_total=4800.0
        ),
        clinical_notes="Critically low Cardiac Index (<1.8 L/min/m2). Requires immediate inotropic and mechanical support.",
        baseline_ecg_rhythm="Sinus Tachycardia with ST Elevations"
    )
}
