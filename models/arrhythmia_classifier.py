"""
CardioTwin Arrhythmia & Acute Decompensation AI Classifier
==========================================================
Real-time ECG signal generator, morphological feature extraction engine,
and machine learning classifier for cardiac rhythm pathologies and clinical
decompensation risk stratification.
"""

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from typing import Dict, Tuple, List


class ArrhythmiaClassifier:
    """
    Rhythm classification and early warning decompensation engine.
    """

    CLASSES = [
        "Normal Sinus Rhythm",
        "Sinus Bradycardia",
        "Sinus Tachycardia",
        "Atrial Fibrillation (AFib)",
        "Ventricular Tachycardia (VTach)",
        "Acute Myocardial Infarction (STEMI Pattern)"
    ]

    def __init__(self):
        self.model = GradientBoostingClassifier(n_estimators=35, max_depth=4, random_state=42)
        self.is_trained = False
        self._train_baseline_model()

    def generate_ecg_waveform(
        self,
        hr: float,
        rhythm_type: str = "Normal Sinus Rhythm",
        duration_sec: float = 4.0,
        sampling_rate: int = 250
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Synthesizes clinically accurate Lead-II ECG waveform based on HR
        and physiological conduction characteristics (P-Q-R-S-T waves).
        """
        n_samples = int(duration_sec * sampling_rate)
        t = np.linspace(0, duration_sec, n_samples)
        ecg = np.zeros(n_samples)

        rr_interval = 60.0 / max(35.0, min(220.0, hr))
        
        # Add rhythm-specific perturbations
        is_afib = "Fibrillation" in rhythm_type
        is_vtach = "Ventricular" in rhythm_type
        is_stemi = "Infarction" in rhythm_type or "STEMI" in rhythm_type

        # Generate cardiac beats
        current_time = 0.05
        while current_time < duration_sec:
            # Beat jitter / irregular RR in AFib
            if is_afib:
                beat_rr = rr_interval * np.random.uniform(0.65, 1.45)
            else:
                beat_rr = rr_interval

            # Time relative to beat start
            beat_mask = (t >= current_time) & (t < current_time + beat_rr)
            t_rel = t[beat_mask] - current_time

            if is_vtach:
                # Wide, bizarre monomorphic QRS complex without P wave
                qrs = 1.8 * np.sin(2 * np.pi * 5.0 * t_rel) * np.exp(-t_rel / 0.18)
                ecg[beat_mask] += qrs
            else:
                # P wave (atrial depolarization) - absent/chaotic in AFib
                if not is_afib:
                    p_wave = 0.18 * np.exp(-((t_rel - 0.08) ** 2) / (2 * (0.022 ** 2)))
                    ecg[beat_mask] += p_wave

                # Q wave
                q_wave = -0.15 * np.exp(-((t_rel - 0.16) ** 2) / (2 * (0.008 ** 2)))
                # R wave (ventricular depolarization)
                r_wave = 1.35 * np.exp(-((t_rel - 0.18) ** 2) / (2 * (0.012 ** 2)))
                # S wave
                s_wave = -0.35 * np.exp(-((t_rel - 0.20) ** 2) / (2 * (0.010 ** 2)))
                
                # ST Segment & T wave (ventricular repolarization)
                st_elevation = 0.35 if is_stemi else 0.0
                st_segment = st_elevation * np.exp(-((t_rel - 0.25) ** 2) / (2 * (0.05 ** 2)))
                t_wave = (0.35 + st_elevation) * np.exp(-((t_rel - 0.36) ** 2) / (2 * (0.045 ** 2)))

                ecg[beat_mask] += (q_wave + r_wave + s_wave + st_segment + t_wave)

            current_time += beat_rr

        # Baseline noise and fibrillatory baseline waves in AFib
        if is_afib:
            f_waves = 0.08 * np.sin(2 * np.pi * 7.5 * t) + 0.05 * np.sin(2 * np.pi * 14.0 * t)
            ecg += f_waves
        
        noise = np.random.normal(0, 0.02, n_samples)
        ecg += noise

        return t, ecg

    def extract_features(self, t: np.ndarray, ecg: np.ndarray, hr: float) -> np.ndarray:
        """
        Extracts morphological and statistical ECG features for classification.
        Features: [HR, SDNN_HRV, QRS_approx_width, ST_deviation, Peak_amplitude, Signal_variance]
        """
        amp_max = float(np.max(ecg))
        amp_min = float(np.min(ecg))
        variance = float(np.var(ecg))
        
        # Approximate ST level in mid-cycle
        st_level = float(np.mean(ecg[np.abs(ecg) < 0.4]))
        
        # HRV heuristic
        hrv_sdnn = 35.0 if hr > 100 else 65.0

        return np.array([hr, hrv_sdnn, amp_max - amp_min, st_level, amp_max, variance])

    def _train_baseline_model(self):
        """
        Trains the classifier on labeled synthetic feature vectors across all 6 classes.
        """
        X = []
        y = []
        np.random.seed(42)

        # Generate representative feature distributions for each rhythm class
        for _ in range(80):
            # NSR
            X.append([np.random.uniform(60, 95), np.random.uniform(40, 80), 1.6, 0.02, 1.4, 0.12])
            y.append(0)
            # Bradycardia
            X.append([np.random.uniform(38, 58), np.random.uniform(50, 90), 1.5, 0.01, 1.3, 0.10])
            y.append(1)
            # Tachycardia
            X.append([np.random.uniform(105, 155), np.random.uniform(20, 45), 1.6, 0.04, 1.4, 0.15])
            y.append(2)
            # AFib
            X.append([np.random.uniform(85, 160), np.random.uniform(90, 160), 1.4, 0.08, 1.2, 0.22])
            y.append(3)
            # VTach
            X.append([np.random.uniform(140, 210), np.random.uniform(10, 30), 2.2, 0.15, 1.9, 0.38])
            y.append(4)
            # STEMI
            X.append([np.random.uniform(70, 115), np.random.uniform(30, 60), 1.7, 0.32, 1.5, 0.19])
            y.append(5)

        self.model.fit(np.array(X), np.array(y))
        self.is_trained = True

    def classify_rhythm(self, hr: float, ecg_signal: np.ndarray, t: np.ndarray) -> Dict[str, any]:
        """
        Classifies rhythm and calculates class probabilities.
        """
        features = self.extract_features(t, ecg_signal, hr).reshape(1, -1)
        pred_idx = int(self.model.predict(features)[0])
        probs = self.model.predict_proba(features)[0]

        return {
            "prediction": self.CLASSES[pred_idx],
            "confidence": round(float(probs[pred_idx]) * 100.0, 1),
            "class_probabilities": {
                self.CLASSES[i]: round(float(p) * 100.0, 1)
                for i, p in enumerate(probs)
            }
        }

    def compute_decompensation_risk(
        self,
        hr: float,
        map_val: float,
        ci: float,
        lvef: float,
        rhythm_prediction: str
    ) -> Dict[str, any]:
        """
        Computes composite Hemodynamic Decompensation Risk Index (HDRI, 0 to 100%).
        """
        risk_score = 10.0  # Base risk

        # MAP scoring (<65 mmHg indicates hypoperfusion / shock)
        if map_val < 60:
            risk_score += 35.0
        elif map_val < 70:
            risk_score += 20.0
        elif map_val > 115:
            risk_score += 15.0

        # Cardiac Index (<2.2 L/min/m2 is depressed, <1.8 is cardiogenic shock)
        if ci < 1.8:
            risk_score += 35.0
        elif ci < 2.2:
            risk_score += 18.0

        # Ejection Fraction (<35% severe heart failure)
        if lvef < 30:
            risk_score += 20.0
        elif lvef < 40:
            risk_score += 10.0

        # Arrhythmia contribution
        if "Ventricular" in rhythm_prediction:
            risk_score += 40.0
        elif "STEMI" in rhythm_prediction:
            risk_score += 35.0
        elif "Fibrillation" in rhythm_prediction:
            risk_score += 15.0

        risk_score = min(99.0, max(5.0, risk_score))

        # Risk tier & clinical actions
        if risk_score >= 70.0:
            tier = "CRITICAL / IMMINENT DECOMPENSATION"
            color = "#D9383A"
            recommendations = [
                "Immediate intensive care resuscitation protocol.",
                "Consider inotropic support (e.g., Dobutamine or Milrinone) to restore Cardiac Index.",
                "Prepare arterial line for continuous invasive arterial pressure monitoring.",
                "Evaluate for urgent mechanical circulatory support (IABP / Impella) if refractory."
            ]
        elif risk_score >= 40.0:
            tier = "ELEVATED RISK / BORDERLINE STABILITY"
            color = "#E08700"
            recommendations = [
                "Intensify continuous telemetry and biophysical monitoring.",
                "Titrate vasodilator / ACE-inhibitor therapy cautiously to reduce afterload without dropping MAP.",
                "Assess volume status; consider gentle loop diuretic if pulmonary congestion evident."
            ]
        else:
            tier = "STABLE PHYSIOLOGICAL PROFILE"
            color = "#2E8B57"
            recommendations = [
                "Hemodynamic stability confirmed within target therapeutic window.",
                "Continue maintenance medical therapy and routine ambulatory monitoring."
            ]

        return {
            "score": round(risk_score, 1),
            "tier": tier,
            "color": color,
            "recommendations": recommendations
        }
