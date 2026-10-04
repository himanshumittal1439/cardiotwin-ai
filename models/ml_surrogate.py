"""
CardioTwin AI / ML Biophysical Surrogate Model
=============================================
Fast machine learning surrogate model trained to approximate complex
cardiovascular biophysical differential equations in sub-milliseconds.
Enables real-time counterfactual drug simulation and parameter sensitivity analysis.
"""

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from typing import Dict, List, Tuple
import os

from models.hemodynamics import PatientHemodynamicState, CardiacDigitalTwinEngine


class BiophysicalSurrogateModel:
    """
    Surrogate ML model trained on biophysical simulations to instantly predict
    Stroke Volume (SV), Ejection Fraction (LVEF), Cardiac Output (CO), and MAP.
    """

    def __init__(self):
        self.model = MultiOutputRegressor(
            RandomForestRegressor(n_estimators=30, max_depth=8, random_state=42)
        )
        self.is_trained = False
        self.feature_names = ["hr", "e_max", "e_min", "v0", "r_sys", "c_art"]
        self.target_names = ["SV", "LVEF", "CO", "MAP", "StrokeWork"]

    def generate_training_data(self, n_samples: int = 150) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates synthetic parameter sweeps across diverse physiological bounds
        and solves the biophysical ODE model to create ground truth training pairs.
        """
        np.random.seed(42)
        X = []
        y = []

        for _ in range(n_samples):
            # Sample physiologically realistic parameters
            hr = float(np.random.uniform(45.0, 150.0))
            e_max = float(np.random.uniform(0.4, 3.5))
            e_min = float(np.random.uniform(0.03, 0.16))
            v0 = float(np.random.uniform(10.0, 45.0))
            r_sys = float(np.random.uniform(0.5, 2.2))
            c_art = float(np.random.uniform(0.5, 2.0))

            state = PatientHemodynamicState(
                hr=hr,
                e_max=e_max,
                e_min=e_min,
                v0=v0,
                r_sys=r_sys,
                c_art=c_art,
                r_ao=0.01,
                r_mi=0.01,
                v_total=5000.0
            )

            engine = CardiacDigitalTwinEngine(state)
            sim = engine.simulate_cardiac_cycle(cycles=2, dt=0.003)
            metrics = engine.compute_clinical_biomarkers(sim)

            X.append([hr, e_max, e_min, v0, r_sys, c_art])
            y.append([
                metrics["SV"],
                metrics["LVEF"],
                metrics["CO"],
                metrics["MAP"],
                metrics["StrokeWork"]
            ])

        return np.array(X), np.array(y)

    def train_or_fit(self, n_samples: int = 120):
        """Trains the surrogate regressor."""
        X, y = self.generate_training_data(n_samples=n_samples)
        self.model.fit(X, y)
        self.is_trained = True

    def predict_hemodynamics(self, state: PatientHemodynamicState) -> Dict[str, float]:
        """
        Instantaneous surrogate inference (< 2 ms) for interactive sliders.
        """
        if not self.is_trained:
            self.train_or_fit()

        features = np.array([[
            state.hr,
            state.e_max,
            state.e_min,
            state.v0,
            state.r_sys,
            state.c_art
        ]])

        pred = self.model.predict(features)[0]
        return {
            name: round(float(pred[idx]), 2)
            for idx, name in enumerate(self.target_names)
        }

    def get_feature_importances(self) -> Dict[str, float]:
        """
        Returns normalized physiological feature importance for Cardiac Output (CO).
        """
        if not self.is_trained:
            self.train_or_fit()

        # The CO regressor is at index 2 of MultiOutputRegressor
        co_estimator = self.model.estimators_[2]
        importances = co_estimator.feature_importances_
        return {
            name: round(float(importances[i]), 3)
            for i, name in enumerate(self.feature_names)
        }
