import unittest
import numpy as np
from wpt.resonator_model import CoupledResonatorEngine, ResonatorParameters
from wpt.parameter_observer import PrimarySideObserver
from wpt.spice_ingest import SpiceWaveformParser


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
        expected_c = 1.0 / ((2.0 * np.pi * 85000.0)**2 * 80.0e-6)
        self.assertAlmostEqual(self.engine.c1, expected_c, places=10)
        self.assertAlmostEqual(self.engine.c2, expected_c, places=10)

    def test_mutual_inductance_bounds(self):
        with self.assertRaises(ValueError):
            self.engine.calculate_mutual_inductance(k=1.2)

        m_nominal = self.engine.calculate_mutual_inductance(k=0.20)
        self.assertAlmostEqual(m_nominal, 16.0e-6, places=8)

    def test_primary_observer_reconstruction_accuracy(self):
        true_k = 0.22
        true_load = 12.0
        omega_res = 2.0 * np.pi * 85000.0

        z_in = self.engine.evaluate_primary_impedance(omega_res, true_k, true_load)
        v_rms = 200.0
        i_rms = v_rms / abs(z_in)
        phase_deg = float(np.degrees(np.angle(z_in)))

        est = self.observer.estimate_link_parameters(
            v_primary_rms=v_rms,
            i_primary_rms=i_rms,
            phase_deg=phase_deg,
            known_secondary_load=true_load
        )

        self.assertAlmostEqual(est["estimated_coupling_k"], true_k, delta=0.01)
        self.assertGreater(est["reflected_resistance_ohm"], 0.0)

    def test_zvs_flag_boundary(self):
        safe_est = self.observer.estimate_link_parameters(200.0, 10.0, phase_deg=8.0)
        self.assertEqual(safe_est["zvs_soft_switching_safe"], 1.0)

        unsafe_est = self.observer.estimate_link_parameters(200.0, 10.0, phase_deg=-4.0)
        self.assertEqual(unsafe_est["zvs_soft_switching_safe"], 0.0)

    def test_spice_transient_quadrature_extraction(self):
        parser = SpiceWaveformParser(target_freq_hz=85000.0)

        # 1 ms duration of 85 kHz excitation (85 full cycles)
        t = np.linspace(0, 0.001, 10000)
        omega = 2.0 * np.pi * 85000.0

        # Switched bridge voltage (fundamental + 3rd harmonic distortion)
        v_raw = 282.8 * np.cos(omega * t) + 40.0 * np.cos(3 * omega * t)
        # Current with 12 deg inductive lag + 5th harmonic switching ripple
        i_raw = 14.14 * np.cos(omega * t - np.radians(12.0)) + 2.0 * np.sin(5 * omega * t)

        extracted = parser.extract_fundamental_phasors(t, v_raw, i_raw)

        self.assertAlmostEqual(extracted.v_rms, 200.0, delta=2.0)
        self.assertAlmostEqual(extracted.i_rms, 10.0, delta=0.2)
        self.assertAlmostEqual(extracted.phase_deg, 12.0, delta=0.5)

        # Confirm integration with the primary-side parameter observer
        obs_result = self.observer.estimate_link_parameters(
            v_primary_rms=extracted.v_rms,
            i_primary_rms=extracted.i_rms,
            phase_deg=extracted.phase_deg,
            known_secondary_load=12.0
        )
        self.assertEqual(obs_result["zvs_soft_switching_safe"], 1.0)


if __name__ == "__main__":
    unittest.main()