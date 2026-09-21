def test_spice_transient_quadrature_extraction(self):
        from wpt.spice_ingest import SpiceWaveformParser
        parser = SpiceWaveformParser(target_freq_hz=85000.0)

        # Synthesize realistic switched inverter data with 3rd harmonic distortion
        t = np.linspace(0, 0.001, 10000)  # 1 ms of 85 kHz data (85 cycles)
        omega = 2.0 * np.pi * 85000.0
        
        # Inverter voltage: fundamental + 3rd harmonic
        v_raw = 282.8 * np.cos(omega * t) + 40.0 * np.cos(3 * omega * t)
        # Current with 12.0 degrees inductive lag + switching ripple
        i_raw = 14.14 * np.cos(omega * t - np.radians(12.0)) + 2.0 * np.sin(5 * omega * t)

        extracted = parser.extract_fundamental_phasors(t, v_raw, i_raw)

        self.assertAlmostEqual(extracted.v_rms, 200.0, delta=2.0)
        self.assertAlmostEqual(extracted.i_rms, 10.0, delta=0.2)
        self.assertAlmostEqual(extracted.phase_deg, 12.0, delta=0.5)

        # Feed directly to observer
        obs_result = self.observer.estimate_link_parameters(
            v_primary_rms=extracted.v_rms,
            i_primary_rms=extracted.i_rms,
            phase_deg=extracted.phase_deg,
            known_secondary_load=12.0
        )
        self.assertEqual(obs_result["zvs_soft_switching_safe"], 1.0)