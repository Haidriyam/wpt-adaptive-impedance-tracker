"""
LTspice / PLECS Transient Waveform Ingest Engine.
Extracts fundamental frequency phasors (V1, I1, phase) from raw switched time-series data.
"""
from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np


@dataclass(frozen=True)
class ExtractedPhasors:
    v_rms: float
    i_rms: float
    phase_deg: float
    frequency_hz: float


class SpiceWaveformParser:
    def __init__(self, target_freq_hz: float = 85000.0):
        self.target_freq_hz = target_freq_hz
        self.omega = 2.0 * np.pi * target_freq_hz

    def extract_fundamental_phasors(
        self,
        time_array: np.ndarray,
        v_primary_array: np.ndarray,
        i_primary_array: np.ndarray
    ) -> ExtractedPhasors:
        """
        Compute fundamental harmonic components using discrete single-bin Fourier quadrature.
        Eliminates switching harmonics (3rd, 5th, 7th) to isolate the true resonant operating point.
        """
        if len(time_array) < 100:
            raise ValueError("Insufficient time-domain sample density for Fourier extraction.")

        # Focus analysis on the final steady-state cycles (last 30% of waveform)
        steady_idx = int(0.70 * len(time_array))
        t_ss = time_array[steady_idx:]
        v_ss = v_primary_array[steady_idx:]
        i_ss = i_primary_array[steady_idx:]

        # Integration basis functions
        sin_basis = np.sin(self.omega * t_ss)
        cos_basis = np.cos(self.omega * t_ss)

        # Numerical integration (trapezoidal quadrature)
        dt = np.mean(np.diff(t_ss))
        total_time = t_ss[-1] - t_ss[0]

        # Voltage Fourier coefficients
        v_real = (2.0 / total_time) * np.sum(v_ss * cos_basis) * dt
        v_imag = (2.0 / total_time) * np.sum(v_ss * sin_basis) * dt
        v_mag_peak = np.sqrt(v_real**2 + v_imag**2)
        v_phase_rad = np.arctan2(v_imag, v_real)

        # Current Fourier coefficients
        i_real = (2.0 / total_time) * np.sum(i_ss * cos_basis) * dt
        i_imag = (2.0 / total_time) * np.sum(i_ss * sin_basis) * dt
        i_mag_peak = np.sqrt(i_real**2 + i_imag**2)
        i_phase_rad = np.arctan2(i_imag, i_real)

        # Compute relative impedance phase displacement
        delta_phase_deg = float(np.degrees(v_phase_rad - i_phase_rad))

        # Normalize phase to [-180, 180]
        delta_phase_deg = (delta_phase_deg + 180.0) % 360.0 - 180.0

        return ExtractedPhasors(
            v_rms=float(v_mag_peak / np.sqrt(2.0)),
            i_rms=float(i_mag_peak / np.sqrt(2.0)),
            phase_deg=delta_phase_deg,
            frequency_hz=self.target_freq_hz
        )