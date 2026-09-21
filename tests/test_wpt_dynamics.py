import unittest
import numpy as np
from wpt.resonator_model import CoupledResonatorEngine, ResonatorParameters
from wpt.parameter_observer import PrimarySideObserver


class TestWPTDynamicsAndObserver(unittest.TestCase):

    def setUp(self):
        self.params = ResonatorParameters(
            f_res_hz=85000.0,
            l1_henry=80.0e-6,
            l2_henry=80.0e-6,
            r1_ohm=0.25,
            r2_ohm=0.28
        )
        self.engine = CoupledResonatorEngine(self.params)
        self.observer = PrimarySideObserver(self.engine)

    def test_series_resonance_capacitance_tuning(self):
        # 1 / (omega0^2 * 80uH) at 85 kHz should be ~43.8 nF
        expected_c = 1.0 / ((2.0 * np.pi * 85000.0)**2 * 80.0e-6)
        self.assertAlmostEqual(self.engine.c1, expected_c, places=10)
        self.assertAlmostEqual(self.engine.c2, expected_c, places=10)

    def test_mutual_inductance_bounds(self):
        with self.assertRaises(ValueError):
            self.engine.calculate_mutual_inductance(k=1.2)  # Non-physical k > 1.0

        m_nominal = self.engine.calculate_mutual_inductance(k=0.20)
        self.assertAlmostEqual(m_nominal, 16.0e-6, places=8)

    def test_primary_observer_reconstruction_accuracy(self):
        # Ground truth operating condition
        true_k = 0.22
        true_load = 12.0  # 12 Ohm load
        omega_res = 2.0 * np.pi * 85000.0

        # Calculate exact analytical input impedance at resonance
        z_in = self.engine.evaluate_primary_impedance(omega_res, true_k, true_load)
        v_rms = 200.0
        i_rms = v_rms / abs(z_in)
        phase_deg = float(np.degrees(np.angle(z_in)))

        # Feed terminal telemetry into the observer
        est = self.observer.estimate_link_parameters(
            v_primary_rms=v_rms,
            i_primary_rms=i_rms,
            phase_deg=phase_deg,
            known_secondary_load=true_load
        )

        # Observer must reconstruct coupling coefficient k within 2% error
        self.assertAlmostEqual(est["estimated_coupling_k"], true_k, delta=0.01)
        self.assertGreater(est["reflected_resistance_ohm"], 0.0)

    def test_zvs_flag_boundary(self):
        # Phase within [3.0, 30.0] must be flagged as safe
        safe_est = self.observer.estimate_link_parameters(200.0, 10.0, phase_deg=8.0)
        self.assertEqual(safe_est["zvs_soft_switching_safe"], 1.0)

        # Negative phase (capacitive) risks GaN bridge shoot-through
        unsafe_est = self.observer.estimate_link_parameters(200.0, 10.0, phase_deg=-4.0)
        self.assertEqual(unsafe_est["zvs_soft_switching_safe"], 0.0)


if __name__ == "__main__":
    unittest.main()