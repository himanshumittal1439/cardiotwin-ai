"""
CardioTwin Architecture Diagram Generator
=========================================
Generates high-resolution architecture diagrams in both PNG and PDF format
for official competition submission.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def generate_architecture_diagram(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(16, 10), dpi=300)
    fig.patch.set_facecolor('#0F172A') # Dark slate background
    ax.set_facecolor('#0F172A')

    # Remove axes
    ax.axis('off')

    # Title Banner
    ax.text(8.0, 9.6, "CardioTwin: Real-Time Biophysical & Neural Digital Twin Architecture",
            fontsize=20, weight='bold', color='#38BDF8', ha='center', va='center')
    ax.text(8.0, 9.2, "End-to-End Computational Pipeline: Multi-Scale Telemetry → Biophysical Solvers → AI Surrogate → Clinical Decision Support",
            fontsize=11, color='#94A3B8', ha='center', va='center')

    # Box styles
    def draw_box(x, y, w, h, title, items, header_bg, body_bg, border_color):
        # Outer Card
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.15",
                                      facecolor=body_bg, edgecolor=border_color, linewidth=1.8)
        ax.add_patch(rect)
        # Header banner
        header = patches.FancyBboxPatch((x, y + h - 0.55), w, 0.55, boxstyle="round,pad=0.05,rounding_size=0.1",
                                        facecolor=header_bg, edgecolor=header_bg)
        ax.add_patch(header)
        ax.text(x + w / 2, y + h - 0.28, title, fontsize=12, weight='bold', color='#FFFFFF', ha='center', va='center')

        # Item text
        cur_y = y + h - 0.85
        for item in items:
            ax.text(x + 0.2, cur_y, item, fontsize=9.5, color='#E2E8F0', va='center')
            cur_y -= 0.38

    # 4 Main Columns (Pipeline flow)
    # 1. Telemetry Ingestion Layer
    col1_items = [
        "• Continuous Lead-II ECG (250 Hz)",
        "• Non-invasive Blood Pressure (SBP/DBP)",
        "• Pulse Oximetry (SpO2) & Heart Rate",
        "• EHR Demographics & BSA (m²)",
        "• Baseline NYHA Functional Class",
        "• Cardiac Biomarkers (Troponin, BNP)"
    ]
    draw_box(0.6, 3.8, 3.2, 4.8, "1. INGESTION LAYER", col1_items, "#0284C7", "#1E293B", "#38BDF8")

    # 2. Biophysical Modeling Core
    col2_items = [
        "• Suga-Sagawa Elastance E(t)",
        "• Double-Hill Activation e_n(t/T)",
        "• 3-Element Windkessel Arterial ODE",
        "• Forward Diode Valve Fluid Dynamics",
        "• Ventricular Volume Conservation",
        "• Real-Time Runge-Kutta Numerical Solver"
    ]
    draw_box(4.3, 3.8, 3.4, 4.8, "2. BIOPHYSICAL ODE CORE", col2_items, "#0D9488", "#1E293B", "#2DD4BF")

    # 3. AI / ML Intelligence Layer
    col3_items = [
        "• MultiOutput Neural Surrogate Model",
        "• Instantaneous Inference (<1.5 ms)",
        "• Gradient Boosted Arrhythmia Classifier",
        "• 6-Class Conduction Detection (AFib, VT)",
        "• Composite Decompensation Risk (HDRI)",
        "• Gini / Tree SHAP Feature Importance"
    ]
    draw_box(8.2, 3.8, 3.4, 4.8, "3. AI / ML SURROGATE LAYER", col3_items, "#D97706", "#1E293B", "#FBBF24")

    # 4. Interactive Clinician Interface
    col4_items = [
        "• Glassmorphic Streamlit UI",
        "• 3D Pulsatile Ventricular Mesh (Plotly)",
        "• Dynamic Multi-Wave Wiggers Diagram",
        "• Dual Baseline-vs-Intervention PV Loops",
        "• In-Silico 'What-If' Drug Titration",
        "• Automated EHR Clinical Dossier Export"
    ]
    draw_box(12.1, 3.8, 3.3, 4.8, "4. CLINICIAN INTERACTION", col4_items, "#E11D48", "#1E293B", "#FB7185")

    # Flow Arrows Between Pillars
    arrow_props = dict(facecolor='#38BDF8', edgecolor='#38BDF8', width=2.5, headwidth=9)
    ax.annotate('', xy=(4.2, 6.2), xytext=(3.9, 6.2), arrowprops=arrow_props)
    ax.annotate('', xy=(8.1, 6.2), xytext=(7.8, 6.2), arrowprops=arrow_props)
    ax.annotate('', xy=(12.0, 6.2), xytext=(11.7, 6.2), arrowprops=arrow_props)

    # Bottom Foundation: Clinical Governance & Safety Guardrails
    gov_items = [
        "FDA SaMD Class IIb Alignment  •  Physician-in-the-Loop Safeguards  •  Zero Local PHI Storage  •  Standardized HL7 / FHIR Interoperability  •  Open-Source MIT License"
    ]
    gov_rect = patches.FancyBboxPatch((0.6, 1.2), 14.8, 1.8, boxstyle="round,pad=0.08,rounding_size=0.15",
                                     facecolor="#1E293B", edgecolor="#64748B", linewidth=1.5)
    ax.add_patch(gov_rect)
    gov_head = patches.FancyBboxPatch((0.6, 2.5), 14.8, 0.5, boxstyle="round,pad=0.05,rounding_size=0.1",
                                      facecolor="#334155", edgecolor="#334155")
    ax.add_patch(gov_head)
    ax.text(8.0, 2.75, "CLINICAL SAFETY, ETHICAL GOVERNANCE & REGULATORY PROTOCOLS",
            fontsize=11.5, weight='bold', color='#F8FAFC', ha='center', va='center')
    ax.text(8.0, 1.85, gov_items[0], fontsize=10.5, color='#94A3B8', ha='center', va='center')

    # Bidirectional Feedback Arrow from Clinician to Biophysical & Surrogate
    feed_arrow = dict(facecolor='#FB7185', edgecolor='#FB7185', width=1.8, headwidth=7)
    ax.annotate('Counterfactual In-Silico Drug Feedback Loop', xy=(6.0, 3.7), xytext=(13.7, 3.7),
                arrowprops=feed_arrow, fontsize=9.5, color='#F43F5E', weight='bold', ha='right', va='top')

    plt.tight_layout()

    # Save PNG and PDF
    png_path = os.path.join(output_dir, "cardiotwin_architecture.png")
    pdf_path = os.path.join(output_dir, "cardiotwin_architecture.pdf")

    plt.savefig(png_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.savefig(pdf_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()

    print(f"Architecture diagram generated:\n- {png_path}\n- {pdf_path}")


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    generate_architecture_diagram(os.path.abspath(out_dir))
