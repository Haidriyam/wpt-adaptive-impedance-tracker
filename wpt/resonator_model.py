"""
Series-Series (SS) Resonant Inductive Power Link Dynamics.
Models primary and secondary high-frequency coupled resonators under SAE J2954.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class ResonatorParameters:
    f_res_hz: float = 85000.0       # 85 kHz nominal operating band
    l1_henry: float = 80.0e-6       # Primary coil inductance (80 uH)
    l2_henry: float = 80.0e-6       # Secondary coil inductance (80 uH)
    r1_ohm: float = 0.25            # Primary parasitic AC ESR
    r2_ohm: float = 0.28            # Secondary parasitic AC ESR


class CoupledResonatorEngine:
    def __init__(self, params: ResonatorParameters = ResonatorParameters()):
        self.params = params
        self.omega_0 = 2.0 * np.pi * self.params.f_res_hz

        # Series compensation tuning: C = 1 / (omega^2 * L)
        self.c1 = 1.0 / (self.omega_0**2 * self.params.l1_henry)
        self.c2 = 1.0 / (self.omega_0**2 * self.params.l2_henry)

    def calculate_mutual_inductance(self, k: float) -> float:
        """Compute mutual inductance M = k * sqrt(L1 * L2)."""
        if not (0.0 <= k <= 1.0):
            raise ValueError(f"Coupling coefficient k must be within [0.0, 1.0], got {k}")
        return float(k * np.sqrt(self.params.l1_henry * self.params.l2_henry))

    def evaluate_primary_impedance(
        self,
        omega: float,
        k: float,
        r_load_ohm: float
    ) -> complex:
        """
        Compute total complex impedance seen by the primary inverter bridge:
        Z_total = Z_1 + Z_ref
        """
        m = self.calculate_mutual_inductance(k)

        # Primary series loop impedance
        z1 = self.params.r1_ohm + 1j * (omega * self.params.l1_henry - 1.0 / (omega * self.c1))

        # Secondary total loop impedance (parasitic resistance + load)
        z2 = (self.params.r2_ohm + r_load_ohm) + 1j * (
            omega * self.params.l2_henry - 1.0 / (omega * self.c2)
        )

        # Reflected impedance into primary
        z_ref = (omega**2 * m**2) / z2
        return complex(z1 + z_ref)

    def evaluate_zvs_phase_angle_deg(
        self,
        omega: float,
        k: float,
        r_load_ohm: float
    ) -> float:
        """
        Extract the phase angle (degrees) of input impedance.
        Inductive region (> 0 deg) is required for GaN Zero-Voltage Switching (ZVS).
        """
        z_in = self.evaluate_primary_impedance(omega, k, r_load_ohm)
        phase_rad = np.angle(z_in)
        return float(np.degrees(phase_rad))