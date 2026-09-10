# UI/UX & Bright Theme Design System Specification

**Project Title**: Quantum-Inspired Cyber Threat Detection for Digital Signature Security (QDS-Framework)  
**Document Version**: 1.0.0  
**Phase**: Phase 1 — Planning & Specification  

---

## 1. Visual Direction: Bright & Scientific Light Theme

The user interface strictly adheres to a **modern, bright, scientific visual aesthetic**. Dark themes, black backgrounds, cyberpunk styling, and neon-on-black accents are explicitly prohibited. The UI visually communicates **advanced technology**, **quantum clarity**, **academic rigor**, and **cybersecurity trust**.

```
  Primary Canvas        Card Panels            Primary Text           Quantum Primary        Legitimate Status
 ┌──────────────┐     ┌──────────────┐       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
 │  #F8FAFC     │     │  #FFFFFF     │       │  #0F172A     │       │  #4F46E5     │       │  #10B981     │
 │  (Slate 50)  │     │  (Pure White)│       │  (Slate 900) │       │ (Indigo 600) │       │ (Emerald 500)│
 └──────────────┘     └──────────────┘       └──────────────┘       └──────────────┘       └──────────────┘

  Quantum Accent       Cyber Cyan Accent      Warning Status         Malicious Status       Border Line
 ┌──────────────┐     ┌──────────────┐       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
 │  #8B5CF6     │     │  #06B6D4     │       │  #F59E0B     │       │  #EF4444     │       │  #E2E8F0     │
 │ (Purple 600) │     │  (Cyan 600)  │       │ (Amber 500)  │       │  (Red 500)   │       │  (Slate 200) │
 └──────────────┘     └──────────────┘       └──────────────┘       └──────────────┘       └──────────────┘
```

---

## 2. Design System Tokens

### 2.1 Color Palette
* **Page Background**: Slate 50 (`#F8FAFC`) — Soft, clean neutral.
* **Surface Background**: Pure White (`#FFFFFF`) — Elevated cards and container panels with crisp borders.
* **Borders & Dividers**: Slate 200 (`#E2E8F0`).
* **Text Hierarchy**:
  * Heading / Primary Body: Slate 900 (`#0F172A`).
  * Subtext / Muted Captions: Slate 600 (`#475569`).
* **Primary Interactive Actions**: Indigo 600 (`#4F46E5`) with hover Indigo 700 (`#4338CA`).
* **Quantum Concept Accents**:
  * Quantum State Purple: Purple 600 (`#8B5CF6`).
  * Teleportation Cyan: Cyan 600 (`#06B6D4`).
* **Security & Status Indicators**:
  * **Legitimate / Accepted**: Emerald 500 (`#10B981`) with soft background Emerald 50 (`#ECFDF5`).
  * **Warning / Suspicious**: Amber 500 (`#F59E0B`) with soft background Amber 50 (`#FFFBEB`).
  * **Malicious / Rejected**: Red 500 (`#EF4444`) with soft background Red 50 (`#FEF2F2`).

### 2.2 Typography & Elevation
* **Font Family**: Inter, System UI, sans-serif.
* **Card Elevation / Shadows**: Soft sub-surface elevation: `box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)`.
* **Border Radius**: Subtle rounded corners (`rounded-xl` / 12px for cards, `rounded-lg` / 8px for buttons and badges).

---

## 3. Page Layouts & Component Hierarchy

The application consists of **9 main pages**:

### 1. Dashboard (Main Workflow Overview)
* **Header**: System Security Health Status Badge (`SYSTEM OPTIMAL` / `ALERT ACTIVE`).
* **Visual Teleportation Workflow Pipeline**: 8-step connected card flow with dynamic status indicators:
  $$\text{User Message} \to \text{Message Processing} \to \text{QDS Encoding} \to \text{Bell Pair} \to \text{Teleportation} \to \text{Pauli Correction} \to \text{Measurement} \to \text{Threat Engine}$$
* **Metric Quick Cards**: Total Verifications, Legitimate Rate (%), Mean State Fidelity, Total Threat Alerts.
* **Recent Activity Feed**: Real-time table of recent signatures and threat evaluations.

### 2. Create Signature (`/create-signature`)
* **Input Panel**: Message input box (e.g., `"Pay ₹100 to Bob"`), sender public key selector.
* **Cryptographic Processing**: Real-time display of SHA-256 binary hash digest.
* **QDS State Encoding Grid**: Visual representation of generated qubit states $|0\rangle, |1\rangle, |+\rangle$.
* **Action Button**: "Generate Signature & Initialize Bell Pairs".

### 3. Teleportation Simulation (`/teleportation`)
* **Interactive Quantum Circuit Visualizer**:
  * Alice's Qubit Line ($S$) & Bell Qubit Line ($A$).
  * Interactive Gate Nodes: $CNOT$, Hadamard ($H$).
  * Classical Transmission Wire carrying $m_1 m_2$ bits to Bob's Line ($B$).
* **Step-by-Step Stepper**: Allows user to step forward/backward through the quantum teleportation mechanics.

### 4. Signature Verification (`/verification`)
* **Bob's Verification Workspace**:
  * Received Classical Measurement Bits $m_1 m_2$.
  * Applied Pauli Correction Matrix ($I, X, Z, XZ$).
  * Reconstructed Qubit State Vector View.
  * Projective Measurement Outcome Distribution (Bar Chart).

### 5. Attack Simulator (`/attack-simulator`)
* **Interactive Attack Injection Console**:
  * Select Threat Vector:
    1. Signature Forgery (Tamper bit values).
    2. Impersonation (Submit invalid sender key).
    3. Replay Attack (Re-send old nonce/session).
    4. Quantum Channel Manipulation (Inject channel bit-flip noise %).
    5. Unauthorized Verification (Exceed rate limit counter).
* **Execute Attack Trigger Button**: Sends manipulated payload to threat engine.

### 6. Threat Detection (`/threat-detection`)
* **Real-time Diagnostic Dashboard**:
  * **State Fidelity Gauge**: Visual meter showing $F \in [0, 1.0]$.
  * **QBER Error Rate Gauge**: Visual meter showing $QBER \in [0\%, 100\%]$.
  * **Protocol Rule Check Matrix**: Checklist showing Anti-Replay Nonce Status, Timestamp Window Delta, Rate Limit Check.
  * **Final Decision Banner**: Large, prominent **LEGITIMATE (ACCEPT)** or **MALICIOUS (REJECT + ALERT)** banner with detailed explanation text.

### 7. Security Analytics (`/analytics`)
* **Recharts Data Visualizations**:
  * **Fidelity & Error Rate Trend Line Chart** over time.
  * **Threat Category Pie Chart** (Forgery vs Replay vs Noise vs Impersonation).
  * **Verification Throughput Area Chart**.

### 8. Threat Logs (`/threat-logs`)
* **Auditable Log Table**:
  * Columns: Timestamp, Session ID, Threat Type, Decision, QBER %, Fidelity, Actions.
  * Search & Filter Controls: Filter by threat vector, date range, or decision status.
  * Modal View: Click row to open full raw JSON diagnostic audit.

### 9. System Architecture & About (`/architecture`)
* **Interactive Architectural Diagram**: Visual view of system layers (Frontend, API Gateway, Quantum Engine, Threat Engine, Database).
* **Linear Algebra Model Reference**: Embedded formula documentation for $H$, $CNOT$, Bell states, and teleportation equations.

---

## 4. Suggested Dashboard Visual Flow

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                             QDS SYSTEM HEALTH: OPTIMAL (100% OPERATIONAL)                              │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                        │
│  [ Step 1: User Message ]       [ Step 2: Processing ]       [ Step 3: Encoding ]       [ Step 4: Bell Pair ]          │
│  ┌──────────────────────┐       ┌────────────────────┐       ┌──────────────────┐       ┌─────────────────────┐        │
│  │ "Pay ₹100 to Bob"    │ ────► │ SHA-256 Digest     │ ────► │ Qubit States     │ ────► │ Bell A ════  Bell B │        │
│  │ Sender: Alice        │       │ a591a6d40...       │       │ |1⟩ |0⟩ |1⟩ ...  │       │ Entangled Resource  │        │
│  └──────────────────────┘       └────────────────────┘       └──────────────────┘       └─────────────────────┘        │
│                                                                                                    │                   │
│                                                                                                    ▼                   │
│  [ Step 8: Final Decision ]     [ Step 7: Detection ]        [ Step 6: Measurement ]    [ Step 5: Teleportation ]      │
│  ┌──────────────────────┐       ┌────────────────────┐       ┌──────────────────┐       ┌─────────────────────┐        │
│  │ LEGITIMATE / ACCEPT  │ ◄──── │ Non-AI Threat Eng  │ ◄──── │ Pauli Correction │ ◄──── │ Alice CNOT + H      │        │
│  │ Status: ACCEPTED     │       │ QBER: 0.0%, F: 1.0 │       │ Bob Apply I/X/Z  │       │ Classical Bits m1m2 │        │
│  └──────────────────────┘       └────────────────────┘       └──────────────────┘       └─────────────────────┘        │
│                                                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```
