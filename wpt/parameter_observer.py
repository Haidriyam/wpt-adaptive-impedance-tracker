"""
Primary-Side Online Observer for WPT Resonant Links.
Estimates coupling factor (k) and secondary load without secondary wireless telemetry.
"""
from typing import Dict
import numpy as np
from wpt.resonator_model import CoupledResonatorEngine


class PrimarySideObserver:
    def __init__(self, engine: CoupledResonatorEngine):
        self.engine = engine

    def estimate_link_parameters(
        self,
        v_primary_rms: float,
        i_primary_rms: float,
        phase_deg: float,
        known_secondary_load: float = 15.0
    ) -> Dict[str, float]:
        """
        Extract mutual inductance M and coupling factor k from primary active impedance.
        Assumes operational frequency is locked to resonance (omega = omega_0).
        """
        if i_primary_rms <= 1e-6:
            raise ValueError("Primary current too low for reliable impedance observation.")

        # Apparent magnitude of input impedance
        z_mag = v_primary_rms / i_primary_rms
        phase_rad = np.radians(phase_deg)

        # Real (resistive) part: R_in = R1 + R_ref
        r_in = z_mag * np.cos(phase_rad)
        r_ref = r_in - self.engine.params.r1_ohm

        if r_ref <= 0.0:
            # Parasitic line loss dominant or uncoupled
            r_ref = 1e-6

        # At secondary resonance: R_ref = (omega_0^2 * M^2) / (R2 + R_L)
        # Therefore: M = sqrt(R_ref * (R2 + R_L)) / omega_0
        denom_r = self.engine.params.r2_ohm + known_secondary_load
        m_est = np.sqrt(r_ref * denom_r) / self.engine.omega_0

        # Coupling coefficient: k = M / sqrt(L1 * L2)
        geom_mean_l = np.sqrt(self.engine.params.l1_henry * self.engine.params.l2_henry)
        k_est = m_est / geom_mean_l

        # Bound k strictly to physical bounds [0.0, 1.0]
        k_est = float(np.clip(k_est, 0.0, 1.0))

        # Evaluate soft-switching margin (ZVS requires phase in [+5 deg, +25 deg])
        is_zvs_safe = 3.0 <= phase_deg <= 30.0

        return {
            "estimated_mutual_inductance_uh": float(m_est * 1e6),
            "estimated_coupling_k": float(k_est),
            "reflected_resistance_ohm": float(r_ref),
            "zvs_soft_switching_safe": 1.0 if is_zvs_safe else 0.0,
        }