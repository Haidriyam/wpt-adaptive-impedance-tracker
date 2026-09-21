![WPT Adaptive Impedance Tracker CI](https://github.com/Haidriyam/wpt-adaptive-impedance-tracker/actions/workflows/devsecops-ci.yml/badge.svg)

# Primary-Side Parameter Observer & ZVS Tracker for 85 kHz Resonant WPT

An analytical, primary-only parameter identification engine for Series-Series (SS) resonant inductive wireless power transfer links under SAE J2954 standards. It tracks mutual inductance ($M$), coupling coefficient ($k$), and Zero-Voltage Switching (ZVS) phase margins in real time without relying on vulnerable secondary-to-primary wireless communication links (BLE / IEEE 802.11p).

```text
[ GaN Bridge Inverter (85 kHz) ] ──► [ Primary Tank: L1, C1 ] ════► [ Secondary Tank: L2, C2 ]
               │                                   ▲                       │
               ▼                                   ║ (Mutual Coupling M)   ▼
    [ Primary Telemetry: V, I, φ ]                 ║             [ Rectifier & Battery ]
               │                                   ▼
               └─────────► [ Primary-Side Parameter Observer ]
                                     │
                                     ├── Extracted Coupling: k
                                     └── Soft-Switching (ZVS) Margin Guard