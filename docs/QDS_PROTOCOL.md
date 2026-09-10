# Quantum Digital Signature (QDS) Protocol Specification

**Project Title**: Quantum-Inspired Cyber Threat Detection for Digital Signature Security (QDS-Framework)  
**Document Version**: 1.0.0  
**Phase**: Phase 1 — Planning & Specification  

---

## 1. Overview & Protocol Objectives

The **Quantum Digital Signature (QDS)** protocol simulates an end-to-end cryptographic digital signature workflow backed by quantum teleportation. The protocol guarantees:
1. **Unforgeability**: Modified message bits or altered quantum state vectors induce state mismatches and measurement errors.
2. **Non-repudiation**: Cryptographic key states tied to sender identity cannot be denied once validated.
3. **Integrity & Teleportation Fidelity**: Teleportation ensures quantum states are recreated at the receiver without transmitting the quantum state itself across an untrusted channel.

---

## 2. Complete Step-by-Step Protocol Workflow

```
[ Alice (Sender) ]                                  [ Classical Channel ]                               [ Bob (Verifier) ]
       │                                                      │                                                  │
 1. Input Message ("Pay ₹100")                                 │                                                  │
       │                                                      │                                                  │
 2. SHA-256 Digest Generation                                 │                                                  │
       │                                                      │                                                  │
 3. Quantum Signature State Encoding                          │                                                  │
    |ψ_1⟩ |ψ_2⟩ ... |ψ_N⟩                                     │                                                  │
       │                                                      │                                                  │
 4. Generate Entangled Bell Pairs ────────────────────────────┼───────────────────────────► Receive Bell B Qubits│
    Receive Bell A Qubits                                     │                                                  │
       │                                                      │                                                  │
 5. Joint Teleportation:                                      │                                                  │
    Apply CNOT(S, A)                                          │                                                  │
    Apply H(S)                                                │                                                  │
    Measure SA -> Classical Bits (m1m2)                       │                                                  │
       │                                                      │                                                  │
 6. Package Metadata Payload ─────────────────────────────────┼───────────────────────────► Receive Session Payload
    (SessionID, Nonce, TS, m1m2, Hash)                        │                                                  │
                                                              │                                7. Check Anti-Replay Cache
                                                              │                                8. Apply Pauli Corrections
                                                              │                                   (I, X, Z, XZ)
                                                              │                                9. Projective Measurement
                                                              │                               10. Fidelity & QBER Audit
                                                              │                               11. ACCEPT / REJECT Decision
```

---

## 3. Detailed Step Breakdown

### STEP 1 — Message Cryptographic Hashing
* The user inputs a text message $M$ (e.g., `"Pay ₹100 to Bob"`).
* The backend computes the SHA-256 digest:
  $$H(M) = \text{SHA-256}(M) \in \{0, 1\}^{256}$$

### STEP 2 — QDS State Encoding
* Each binary bit $b_k \in H(M)$ is mapped to a quantum state vector $|\psi_k\rangle$:
  * If $b_k = 0 \implies |\psi_k\rangle = |0\rangle = \begin{bmatrix} 1 \\ 0 \end{bmatrix}$
  * If $b_k = 1 \implies |\psi_k\rangle = |1\rangle = \begin{bmatrix} 0 \\ 1 \end{bmatrix}$
* Optional basis rotation: Phase-encoded states can be created using Hadamard or rotation operators $R_y(\theta)$ to enhance signature complexity.

### STEP 3 — Entangled Bell Pair Generation
* The Quantum Engine initializes $N$ independent entangled Bell pairs $|\Phi^+\rangle_{AB} = \frac{1}{\sqrt{2}}(|00\rangle_{AB} + |11\rangle_{AB})$.
* **Distribution**:
  * Qubit $A_k$ is allocated to Alice (Sender).
  * Qubit $B_k$ is allocated to Bob (Verifier).

### STEP 4 — Alice Teleportation Execution
For each signature state $|\psi_k\rangle_S$ and Bell qubit $A_k$:
1. Alice executes $CNOT$ with control qubit $S_k$ and target qubit $A_k$.
2. Alice executes Hadamard gate $H$ on control qubit $S_k$.
3. Alice performs projective measurement on $S_k$ and $A_k$, producing classical bits $m_1^{(k)} m_2^{(k)} \in \{00, 01, 10, 11\}$.

### STEP 5 — Classical Transmission & Metadata Encapsulation
Alice constructs a session payload $\mathcal{P}_{session}$ sent via classical HTTP/REST API to Bob:

$$\mathcal{P}_{session} = \left\{ \text{session\_id}, \text{nonce}, \text{timestamp}, H(M), [m_1^{(1)} m_2^{(1)}, \dots, m_1^{(N)} m_2^{(N)}], \text{sender\_pk\_hash} \right\}$$

#### Session Metadata Schema:
* `session_id`: Unique UUIDv4 identifying the signature session.
* `nonce`: 128-bit random hex string for anti-replay enforcement.
* `timestamp`: Unix UTC timestamp in milliseconds.
* `classical_bits`: Array of measurement bit pairs $m_1 m_2$.
* `attempt_count`: Counter tracking total verification requests for this session.

### STEP 6 — Bob Pauli Correction & State Reconstruction
For each received classical bit pair $m_1^{(k)} m_2^{(k)}$, Bob applies unitary Pauli correction $U_B^{(k)}$ on Bell qubit $B_k$:

$$U_B^{(k)} = \begin{cases} 
I = \begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix} & \text{if } m_1 m_2 = 00 \\[6pt]
X = \begin{bmatrix} 0 & 1 \\ 1 & 0 \end{bmatrix} & \text{if } m_1 m_2 = 01 \\[6pt]
Z = \begin{bmatrix} 1 & 0 \\ 0 & -1 \end{bmatrix} & \text{if } m_1 m_2 = 10 \\[6pt]
X Z = \begin{bmatrix} 0 & -1 \\ 1 & 0 \end{bmatrix} & \text{if } m_1 m_2 = 11 
\end{cases}$$

After Pauli correction, Bob's qubit $B_k$ collapses into the reconstructed state $|\psi_{rec}^{(k)}\rangle$.

### STEP 7 — Verification & Projective Measurement
Bob measures state $|\psi_{rec}^{(k)}\rangle$ using projective measurement operators $M_0, M_1$ and compares observed outcomes against expected state outcomes computed from $H(M)$.

---

## 4. Security Metrics Computed

1. **State Fidelity ($F$)**:
   $$F_k = |\langle \psi_{exp}^{(k)} | \psi_{rec}^{(k)} \rangle|^2, \quad \bar{F} = \frac{1}{N} \sum_{k=1}^N F_k$$

2. **Quantum Bit Error Rate ($QBER$)**:
   $$QBER = \frac{\text{Number of Mismatched Measurement Outcomes}}{N} \times 100\%$$

3. **Protocol Validation**:
   * Nonce freshness check ($\text{nonce} \notin \text{SessionCache}$).
   * Timestamp delta limit ($\Delta t \le 300\text{ seconds}$).
