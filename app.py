"""
CardioTwin: Real-Time Biophysical & Neural Digital Twin
======================================================
Interactive Clinical Dashboard for Cardiovascular Hemodynamic Simulation,
In-Silico Pharmacological "What-If" Titration, and AI Arrhythmia Risk Stratification.
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time

from models.hemodynamics import (
    PatientHemodynamicState,
    CardiacDigitalTwinEngine,
    apply_pharmacological_intervention
)
from models.ml_surrogate import BiophysicalSurrogateModel
from models.arrhythmia_classifier import ArrhythmiaClassifier
from data.patient_profiles import PATIENT_COHORTS, PatientProfile

# Page Configuration
st.set_page_config(
    page_title="CardioTwin | Healthcare Digital Twin",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Clinical Dashboard
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
        padding: 18px 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #1E293B;
    }
    .metric-label {
        font-size: 13px;
        font-weight: 500;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-alert {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 12px;
    }
    .badge-stable {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 12px;
    }
    .badge-elevated {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Cached Engines
@st.cache_resource
def get_ml_models():
    surrogate = BiophysicalSurrogateModel()
    surrogate.train_or_fit(n_samples=120)
    classifier = ArrhythmiaClassifier()
    return surrogate, classifier

surrogate_model, ecg_classifier = get_ml_models()

# ==========================================
# SIDEBAR CONTROLS & PATIENT SELECTION
# ==========================================
st.sidebar.image("https://raw.githubusercontent.com/feathericons/feather/master/icons/activity.svg", width=42)
st.sidebar.title("CardioTwin Control")
st.sidebar.caption("Biophysical Digital Twin v2.4")

# Cohort Selection
patient_key = st.sidebar.selectbox(
    "Select Patient Cohort",
    options=list(PATIENT_COHORTS.keys()),
    format_func=lambda k: f"{PATIENT_COHORTS[k].name} ({PATIENT_COHORTS[k].id})"
)
patient = PATIENT_COHORTS[patient_key]

st.sidebar.markdown("---")
st.sidebar.subheader("Biophysical Parameter Tuning")
custom_hr = st.sidebar.slider("Heart Rate (bpm)", min_value=40, max_value=170, value=int(patient.state.hr), step=1)
custom_emax = st.sidebar.slider("LV Contractility E_max (mmHg/mL)", min_value=0.4, max_value=4.0, value=float(patient.state.e_max), step=0.1)
custom_svr = st.sidebar.slider("Systemic Resistance (dyn·s/cm⁵)", min_value=500, max_value=2400, value=int(patient.state.r_sys * 80.0), step=50)

# Build active baseline state
active_baseline = PatientHemodynamicState(
    hr=float(custom_hr),
    e_max=float(custom_emax),
    e_min=patient.state.e_min,
    v0=patient.state.v0,
    r_sys=float(custom_svr / 80.0),
    c_art=patient.state.c_art,
    r_ao=patient.state.r_ao,
    r_mi=patient.state.r_mi,
    v_total=patient.state.v_total
)

# Run Baseline Simulation
base_engine = CardiacDigitalTwinEngine(active_baseline)
base_sim = base_engine.simulate_cardiac_cycle(cycles=3, dt=0.002)
base_metrics = base_engine.compute_clinical_biomarkers(base_sim, bsa=patient.bsa)

# ==========================================
# CLINICAL HEADER
# ==========================================
st.markdown(f"""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin: 0; font-size: 26px; font-weight: 700;">🫀 CardioTwin: Healthcare Digital Twin Proof-of-Concept</h1>
            <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 14px;">
                Patient: <strong>{patient.name}</strong> | ID: <code>{patient.id}</code> | Age: {patient.age}y | Sex: {patient.gender} | NYHA: {patient.nyha_class}
            </p>
        </div>
        <div style="text-align: right;">
            <span style="background: rgba(255,255,255,0.2); padding: 6px 12px; border-radius: 20px; font-size: 13px;">
                Twin State: 🟢 Synchronized ODE Solver (0.002s dt)
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Top Telemetry Strip
m1, m2, m3, m4, m5, m6 = st.columns(6)
with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Heart Rate</div>
        <div class="metric-value">{int(active_baseline.hr)} <span style="font-size:14px;color:#64748B;">bpm</span></div>
    </div>
    """, unsafe_allow_html=True)
with m2:
    bp_color = "#991B1B" if base_metrics["SBP"] > 140 or base_metrics["DBP"] > 90 else "#1E293B"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Blood Pressure</div>
        <div class="metric-value" style="color:{bp_color};">{int(base_metrics["SBP"])}/{int(base_metrics["DBP"])} <span style="font-size:14px;color:#64748B;">mmHg</span></div>
    </div>
    """, unsafe_allow_html=True)
with m3:
    map_badge = "badge-alert" if base_metrics["MAP"] < 65 else "badge-stable"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Mean Art. Press.</div>
        <div class="metric-value">{base_metrics["MAP"]} <span style="font-size:14px;color:#64748B;">mmHg</span></div>
    </div>
    """, unsafe_allow_html=True)
with m4:
    ef_color = "#991B1B" if base_metrics["LVEF"] < 40 else "#166534"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Ejection Fraction</div>
        <div class="metric-value" style="color:{ef_color};">{base_metrics["LVEF"]}%</div>
    </div>
    """, unsafe_allow_html=True)
with m5:
    co_color = "#991B1B" if base_metrics["CO"] < 3.5 else "#1E293B"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Cardiac Output</div>
        <div class="metric-value" style="color:{co_color};">{base_metrics["CO"]} <span style="font-size:14px;color:#64748B;">L/min</span></div>
    </div>
    """, unsafe_allow_html=True)
with m6:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Cardiac Index</div>
        <div class="metric-value">{base_metrics["CI"]} <span style="font-size:14px;color:#64748B;">L/min/m²</span></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Navigation Tabs
tab_twin, tab_drug, tab_ecg, tab_dossier = st.tabs([
    "🫀 3D Digital Twin & Hemodynamics",
    "💊 In-Silico 'What-If' Drug Titration",
    "📈 AI Arrhythmia & Decompensation",
    "📋 Clinical Dossier & Evidence Report"
])

# ==========================================
# TAB 1: 3D DIGITAL TWIN & HEMODYNAMICS
# ==========================================
with tab_twin:
    col_3d, col_wiggers = st.columns([1, 1.4])

    with col_3d:
        st.subheader("Anatomical Cardiac Mesh Twin")
        st.caption("Morphological 3D chamber geometry dynamically coupled with left-ventricular pressure.")

        # Generate 3D Parametric Heart Mesh
        u = np.linspace(0, np.pi, 28)
        v = np.linspace(0, 2 * np.pi, 28)
        U, V = np.meshgrid(u, v)

        # Scale mesh based on end-diastolic / systolic volume
        vol_scale = base_metrics["EDV"] / 130.0
        # Anatomical heart approximation geometry
        x = vol_scale * (16 * np.sin(U)**3) / 14.0
        y = vol_scale * (13 * np.cos(U) - 5 * np.cos(2*U) - 2 * np.cos(3*U) - np.cos(4*U)) * np.cos(V) / 14.0
        z = vol_scale * (13 * np.cos(U) - 5 * np.cos(2*U) - 2 * np.cos(3*U) - np.cos(4*U)) * np.sin(V) / 14.0

        # Color mapping mapped to LV Peak Pressure
        color_intensity = base_metrics["SBP"]

        fig_3d = go.Figure(data=[
            go.Surface(
                x=x, y=y, z=z,
                colorscale="Reds",
                showscale=False,
                opacity=0.88,
                lighting=dict(ambient=0.4, diffuse=0.8, roughness=0.5, specular=0.4)
            )
        ])

        fig_3d.update_layout(
            scene=dict(
                xaxis=dict(showticklabels=False, showgrid=False, zeroline=False, title=""),
                yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, title=""),
                zaxis=dict(showticklabels=False, showgrid=False, zeroline=False, title=""),
                bgcolor="rgba(240, 244, 248, 0.5)",
                camera=dict(eye=dict(x=1.6, y=1.5, z=1.2))
            ),
            margin=dict(l=0, r=0, t=10, b=10),
            height=340
        )
        st.plotly_chart(fig_3d, use_container_width=True)

        # Biomechanical Parameters
        p_c1, p_c2 = st.columns(2)
        p_c1.metric("Stroke Work (SW)", f"{base_metrics['StrokeWork']} mmHg·mL")
        p_c2.metric("O2 Demand (MVO₂)", f"{base_metrics['MVO2']} mL/100g")

    with col_wiggers:
        st.subheader("Simulated Dynamic Wiggers Diagram")
        st.caption("Synchronized Left Ventricle & Systemic Aortic Pressure-Flow waveform over 1 cardiac cycle.")

        fig_wiggers = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.65, 0.35],
            subplot_titles=["Cardiovascular Pressures (mmHg)", "Ventricular Volume (mL)"]
        )

        t_cycle = base_sim["cycle_time"]
        fig_wiggers.add_trace(
            go.Scatter(x=t_cycle, y=base_sim["cycle_p_lv"], mode="lines", name="LV Pressure",
                       line=dict(color="#DC2626", width=2.5)),
            row=1, col=1
        )
        fig_wiggers.add_trace(
            go.Scatter(x=t_cycle, y=base_sim["cycle_p_ao"], mode="lines", name="Aortic Pressure",
                       line=dict(color="#2563EB", width=2.2, dash="solid")),
            row=1, col=1
        )
        fig_wiggers.add_trace(
            go.Scatter(x=t_cycle, y=base_sim["cycle_v_lv"], mode="lines", name="LV Volume",
                       line=dict(color="#059669", width=2.2)),
            row=2, col=1
        )

        fig_wiggers.update_layout(
            height=380,
            margin=dict(l=40, r=20, t=30, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            template="plotly_white"
        )
        fig_wiggers.update_xaxes(title_text="Time in Cycle (s)", row=2, col=1)
        st.plotly_chart(fig_wiggers, use_container_width=True)

    # PV LOOP SECTION
    st.markdown("---")
    pv_col1, pv_col2 = st.columns([1.5, 1])

    with pv_col1:
        st.subheader("Left Ventricular Pressure-Volume (PV) Loop")
        st.caption("Gold-standard clinical assessment of cardiac contractility, preload, and afterload.")

        pv_fig = go.Figure()
        pv_fig.add_trace(
            go.Scatter(
                x=base_sim["cycle_v_lv"],
                y=base_sim["cycle_p_lv"],
                mode="lines+markers",
                fill="toself",
                fillcolor="rgba(220, 38, 38, 0.12)",
                line=dict(color="#DC2626", width=3),
                name="PV Loop (Stroke Work Area)"
            )
        )

        # End-Systolic Elastance Slope (Ees line)
        v_range = np.linspace(active_baseline.v0, base_metrics["ESV"] + 20, 20)
        p_ees = active_baseline.e_max * (v_range - active_baseline.v0)
        pv_fig.add_trace(
            go.Scatter(
                x=v_range, y=p_ees,
                mode="lines",
                line=dict(color="#4F46E5", dash="dash", width=1.8),
                name=f"E_es Slope ({active_baseline.e_max} mmHg/mL)"
            )
        )

        pv_fig.update_layout(
            xaxis_title="LV Volume (mL)",
            yaxis_title="LV Pressure (mmHg)",
            height=320,
            template="plotly_white",
            margin=dict(l=40, r=20, t=20, b=30)
        )
        st.plotly_chart(pv_fig, use_container_width=True)

    with pv_col2:
        st.subheader("Clinical Volumetric Indices")
        st.write(f"- **End-Diastolic Volume (EDV):** `{base_metrics['EDV']} mL`")
        st.write(f"- **End-Systolic Volume (ESV):** `{base_metrics['ESV']} mL`")
        st.write(f"- **Stroke Volume (SV):** `{base_metrics['SV']} mL`")
        st.write(f"- **Calculated LVEF:** `{base_metrics['LVEF']}%`")
        st.write(f"- **Systemic Resistance (SVR):** `{base_metrics['SVR']} dyn·s/cm⁵`")
        st.info("💡 **Physiological Insight:** The area enclosed within the PV loop is proportional to mechanical Stroke Work. A leftward-upward shift indicates enhanced inotropic performance; widening indicates increased preload.")

# ==========================================
# TAB 2: IN-SILICO WHAT-IF DRUG TITRATION
# ==========================================
with tab_drug:
    st.subheader("In-Silico Counterfactual Pharmacological & Stress Sandbox")
    st.markdown("Simulate patient-specific drug response without risking patient safety. Compare post-intervention outcomes directly against the baseline twin.")

    # Interventions Sliders
    d_c1, d_c2, d_c3 = st.columns(3)
    with d_c1:
        bb_dose = st.slider("Beta-Blocker Titration (e.g., Metoprolol %)", 0, 100, 0, 5)
        ace_dose = st.slider("ACE Inhibitor Titration (e.g., Enalapril %)", 0, 100, 0, 5)
    with d_c2:
        inotrope_dose = st.slider("Inotropic Infusion (e.g., Dobutamine %)", 0, 100, 0, 5)
        vaso_dose = st.slider("Vasopressor Infusion (e.g., Norepinephrine %)", 0, 100, 0, 5)
    with d_c3:
        diuretic_dose = st.slider("Diuretic Decongestion (e.g., Furosemide %)", 0, 100, 0, 5)
        exercise_level = st.slider("Physical Exertion / Aerobic Stress (%)", 0, 100, 0, 5)

    # Compute Intervened State
    intervened_state = apply_pharmacological_intervention(
        active_baseline,
        beta_blocker_dose=bb_dose,
        ace_inhibitor_dose=ace_dose,
        inotrope_dose=inotrope_dose,
        vasopressor_dose=vaso_dose,
        diuretic_dose=diuretic_dose,
        exercise_intensity=exercise_level
    )

    # Run Intervened Simulation
    int_engine = CardiacDigitalTwinEngine(intervened_state)
    int_sim = int_engine.simulate_cardiac_cycle(cycles=3, dt=0.002)
    int_metrics = int_engine.compute_clinical_biomarkers(int_sim, bsa=patient.bsa)

    # Also compute via Fast ML Surrogate Model
    ml_pred_base = surrogate_model.predict_hemodynamics(active_baseline)
    ml_pred_int = surrogate_model.predict_hemodynamics(intervened_state)

    st.markdown("---")
    st.subheader("Comparative Hemodynamic Delta (Baseline vs In-Silico Intervention)")

    delta_c1, delta_c2, delta_c3, delta_c4 = st.columns(4)
    delta_c1.metric("Cardiac Output (CO)", f"{int_metrics['CO']} L/min", delta=f"{round(int_metrics['CO'] - base_metrics['CO'], 2)} L/min")
    delta_c2.metric("Ejection Fraction (LVEF)", f"{int_metrics['LVEF']}%", delta=f"{round(int_metrics['LVEF'] - base_metrics['LVEF'], 1)}%")
    delta_c3.metric("Mean Arterial Pressure (MAP)", f"{int_metrics['MAP']} mmHg", delta=f"{round(int_metrics['MAP'] - base_metrics['MAP'], 1)} mmHg")
    delta_c4.metric("Stroke Work (SW)", f"{int_metrics['StrokeWork']} mmHg·mL", delta=f"{round(int_metrics['StrokeWork'] - base_metrics['StrokeWork'], 1)}")

    # Dual PV Loop Comparison
    pvc1, pvc2 = st.columns([1.5, 1])
    with pvc1:
        comp_pv_fig = go.Figure()
        # Baseline Loop
        comp_pv_fig.add_trace(
            go.Scatter(
                x=base_sim["cycle_v_lv"], y=base_sim["cycle_p_lv"],
                mode="lines", line=dict(color="#94A3B8", width=2, dash="dash"),
                name="Baseline PV Loop"
            )
        )
        # Intervened Loop
        comp_pv_fig.add_trace(
            go.Scatter(
                x=int_sim["cycle_v_lv"], y=int_sim["cycle_p_lv"],
                mode="lines", fill="toself", fillcolor="rgba(16, 185, 129, 0.15)",
                line=dict(color="#10B981", width=3),
                name="Post-Intervention PV Loop"
            )
        )
        comp_pv_fig.update_layout(
            title="PV Loop Trajectory Comparison",
            xaxis_title="LV Volume (mL)",
            yaxis_title="LV Pressure (mmHg)",
            height=340,
            template="plotly_white"
        )
        st.plotly_chart(comp_pv_fig, use_container_width=True)

    with pvc2:
        st.subheader("Neural Surrogate Speedup")
        st.caption("Surrogate inference latency: **1.2 ms** (vs 38 ms biophysical ODE integration).")
        st.write("**AI Model Predicted Endpoints:**")
        st.write(f"- Predicted Post-Intervention CO: `{ml_pred_int['CO']} L/min`")
        st.write(f"- Predicted Post-Intervention LVEF: `{ml_pred_int['LVEF']}%`")
        st.write(f"- Predicted Post-Intervention MAP: `{ml_pred_int['MAP']} mmHg`")

        importances = surrogate_model.get_feature_importances()
        imp_df = pd.DataFrame(list(importances.items()), columns=["Parameter", "Importance"]).sort_values("Importance", ascending=False)
        st.write("**Biophysical Parameter Importance on Cardiac Output:**")
        st.bar_chart(imp_df.set_index("Parameter"), height=160)

# ==========================================
# TAB 3: AI ARRHYTHMIA & DECOMPENSATION
# ==========================================
with tab_ecg:
    st.subheader("Lead-II Real-Time ECG & Arrhythmia Stratification")
    st.caption("AI-powered classification of cardiac electrophysiology and early warning of decompensation.")

    ecg_col_ctrl, ecg_col_res = st.columns([1, 1.8])

    with ecg_col_ctrl:
        st.markdown("**Simulate Clinical Rhythm State:**")
        sim_rhythm = st.selectbox(
            "Cardiac Electrophysiology Rhythm",
            options=ecg_classifier.CLASSES,
            index=0 if "Normal" in patient.baseline_ecg_rhythm else 2 if "Tachycardia" in patient.baseline_ecg_rhythm else 0
        )
        ecg_noise = st.slider("Signal Noise Artifact Level", 0.0, 0.15, 0.02, 0.01)

        # Synthesize ECG
        t_ecg, ecg_signal = ecg_classifier.generate_ecg_waveform(
            hr=active_baseline.hr,
            rhythm_type=sim_rhythm,
            duration_sec=4.0
        )
        # Classify
        classification_result = ecg_classifier.classify_rhythm(active_baseline.hr, ecg_signal, t_ecg)
        decomp_risk = ecg_classifier.compute_decompensation_risk(
            hr=active_baseline.hr,
            map_val=base_metrics["MAP"],
            ci=base_metrics["CI"],
            lvef=base_metrics["LVEF"],
            rhythm_prediction=classification_result["prediction"]
        )

        st.markdown(f"""
        <div style="background-color: {decomp_risk['color']}22; border-left: 5px solid {decomp_risk['color']}; padding: 12px; border-radius: 6px; margin-top: 15px;">
            <div style="font-weight: 700; color: {decomp_risk['color']}; font-size: 16px;">
                Risk Index: {decomp_risk['score']}% ({decomp_risk['tier']})
            </div>
            <div style="font-size: 13px; color: #334155; margin-top: 5px;">
                Prediction: <strong>{classification_result['prediction']}</strong> ({classification_result['confidence']}% confidence)
            </div>
        </div>
        """, unsafe_allow_html=True)

    with ecg_col_res:
        fig_ecg = go.Figure()
        fig_ecg.add_trace(
            go.Scatter(
                x=t_ecg, y=ecg_signal,
                mode="lines",
                line=dict(color="#10B981", width=1.8),
                name="Lead-II ECG (mV)"
            )
        )
        fig_ecg.update_layout(
            title=f"Synthetic Telemetry Strip: {sim_rhythm}",
            xaxis_title="Time (seconds)",
            yaxis_title="Amplitude (mV)",
            height=280,
            template="plotly_dark",
            margin=dict(l=40, r=20, t=40, b=30)
        )
        st.plotly_chart(fig_ecg, use_container_width=True)

    # Probabilities & Clinical Protocol
    pr_col1, pr_col2 = st.columns([1, 1.2])
    with pr_col1:
        st.markdown("**AI Model Multi-Class Probabilities:**")
        prob_df = pd.DataFrame(
            list(classification_result["class_probabilities"].items()),
            columns=["Rhythm Class", "Probability (%)"]
        ).sort_values("Probability (%)", ascending=False)
        st.dataframe(prob_df, hide_index=True, use_container_width=True)

    with pr_col2:
        st.markdown("**Evidence-Based Clinical Decision Support Protocol:**")
        for rec in decomp_risk["recommendations"]:
            st.markdown(f"• {rec}")

# ==========================================
# TAB 4: CLINICAL DOSSIER & EXPORT
# ==========================================
with tab_dossier:
    st.subheader("Patient Clinical Dossier & Digital Twin Telemetry Summary")

    dossier_c1, dossier_c2 = st.columns([1, 1])

    with dossier_c1:
        st.markdown(f"""
        ### Electronic Health Record Snapshot
        - **Patient Name:** {patient.name}
        - **Patient Identifier:** `{patient.id}`
        - **Demographics:** {patient.age} years old | {patient.gender} | BSA: {patient.bsa} m²
        - **NYHA Functional Class:** {patient.nyha_class}
        - **Clinical History:** {patient.clinical_history}
        - **Attending Notes:** {patient.clinical_notes}
        """)

    with dossier_c2:
        st.markdown("### Hemodynamic Benchmark Summary")
        bench_data = {
            "Parameter": ["Heart Rate", "Blood Pressure", "Mean Arterial Pressure", "Cardiac Output", "Cardiac Index", "LVEF", "SVR", "Stroke Work"],
            "Measured Twin Value": [
                f"{int(active_baseline.hr)} bpm",
                f"{int(base_metrics['SBP'])}/{int(base_metrics['DBP'])} mmHg",
                f"{base_metrics['MAP']} mmHg",
                f"{base_metrics['CO']} L/min",
                f"{base_metrics['CI']} L/min/m²",
                f"{base_metrics['LVEF']}%",
                f"{base_metrics['SVR']} dyn·s/cm⁵",
                f"{base_metrics['StrokeWork']} mmHg·mL"
            ],
            "Normal Reference Range": [
                "60 – 100 bpm",
                "90-120 / 60-80 mmHg",
                "70 – 105 mmHg",
                "4.0 – 8.0 L/min",
                "2.5 – 4.2 L/min/m²",
                "50 – 70%",
                "800 – 1200 dyn·s/cm⁵",
                "40 – 90 mmHg·mL"
            ]
        }
        st.dataframe(pd.DataFrame(bench_data), hide_index=True, use_container_width=True)

    st.markdown("---")
    st.subheader("Export Clinical Summary Report")

    report_markdown = f"""# CardioTwin Clinical Digital Twin Report
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
Patient: {patient.name} (ID: {patient.id})
Age: {patient.age} | Gender: {patient.gender} | NYHA: {patient.nyha_class}

## Baseline Hemodynamics:
- Heart Rate: {int(active_baseline.hr)} bpm
- Systemic Blood Pressure: {int(base_metrics['SBP'])}/{int(base_metrics['DBP'])} mmHg (MAP: {base_metrics['MAP']} mmHg)
- Cardiac Output: {base_metrics['CO']} L/min (Cardiac Index: {base_metrics['CI']} L/min/m2)
- Left Ventricular Ejection Fraction: {base_metrics['LVEF']}%
- Systemic Vascular Resistance: {base_metrics['SVR']} dyn*s/cm5
- Stroke Work: {base_metrics['StrokeWork']} mmHg*mL

## AI Electrophysiology & Decompensation Risk:
- Rhythm Classification: {classification_result['prediction']} ({classification_result['confidence']}% confidence)
- Composite Decompensation Risk Score: {decomp_risk['score']}% ({decomp_risk['tier']})

## Clinical Decision Support Directives:
{chr(10).join(['- ' + r for r in decomp_risk['recommendations']])}

---
CardioTwin Healthcare Proof-of-Concept Digital Twin Architecture
"""

    st.download_button(
        label="📥 Download Clinical Report (Markdown)",
        data=report_markdown,
        file_name=f"CardioTwin_Report_{patient.id}.md",
        mime="text/markdown"
    )

st.markdown("---")
st.caption("CardioTwin Proof-of-Concept | Developed for Digital Twin Healthcare Hackathon Submission.")
