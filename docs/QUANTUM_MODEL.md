# Quantum Mathematical Model & Linear Algebra Specification

**Project Title**: Quantum-Inspired Cyber Threat Detection for Digital Signature Security (QDS-Framework)  
**Document Version**: 1.0.0  
**Phase**: Phase 1 — Planning & Specification  

---

## 1. Single-Qubit Representation

In quantum mechanics, a qubit is represented as a unit vector in a 2-dimensional complex Hilbert space $\mathbb{C}^2$. The computational basis states $|0\rangle$ and $|1\rangle$ are defined as column vectors:

$$|0\rangle = \begin{bmatrix} 1 \\ 0 \end{bmatrix}, \quad |1\rangle = \begin{bmatrix} 0 \\ 1 \end{bmatrix}$$

An arbitrary single-qubit quantum state $|\psi\rangle$ is a linear superposition of the basis states:

$$|\psi\rangle = \alpha |0\rangle + \beta |1\rangle = \begin{bmatrix} \alpha \\ \beta \end{bmatrix}, \quad \alpha, \beta \in \mathbb{C}$$

### Normalization Condition
The state vector must satisfy the probability normalization constraint:

$$\langle \psi | \psi \rangle = |\alpha|^2 + |\beta|^2 = 1$$

where $\langle \psi | = \begin{bmatrix} \alpha^* & \beta^* \end{bmatrix}$ is the conjugate transpose (bra vector) of $|\psi\rangle$.

---

## 2. Quantum Gate Operations & Matrix Representations

Quantum gates are represented by $2^n \times 2^n$ unitary matrices $U$ acting on $n$-qubit state vectors, satisfying $U^\dagger U = U U^\dagger = I$.

### 2.1 Identity Matrix ($I$)
$$I = \begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix}$$

### 2.2 Pauli Matrices ($X, Y, Z$)
The Pauli matrices represent fundamental bit-flip, phase-flip, and combined bit-phase flip operations:

* **Pauli-X (Bit Flip / NOT Gate)**:
  $$X = \begin{bmatrix} 0 & 1 \\ 1 & 0 \end{bmatrix}, \quad X|0\rangle = |1\rangle, \quad X|1\rangle = |0\rangle$$

* **Pauli-Y (Bit and Phase Flip)**:
  $$Y = \begin{bmatrix} 0 & -i \\ i & 0 \end{bmatrix}, \quad Y|0\rangle = i|1\rangle, \quad Y|1\rangle = -i|0\rangle$$

* **Pauli-Z (Phase Flip)**:
  $$Z = \begin{bmatrix} 1 & 0 \\ 0 & -1 \end{bmatrix}, \quad Z|0\rangle = |0\rangle, \quad Z|1\rangle = -|1\rangle$$

### 2.3 Hadamard Gate ($H$)
The Hadamard gate creates an equal superposition of $|0\rangle$ and $|1\rangle$:

$$H = \frac{1}{\sqrt{2}} \begin{bmatrix} 1 & 1 \\ 1 & -1 \end{bmatrix}$$

$$H|0\rangle = |+\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle), \quad H|1\rangle = |-\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle)$$

### 2.4 Controlled-NOT Gate ($CNOT$)
The 2-qubit $CNOT$ gate flips the target qubit if and only if the control qubit is $|1\rangle$. In the 4-dimensional computational basis $\{|00\rangle, |01\rangle, |10\rangle, |11\rangle\}$, its matrix is:

$$CNOT = \begin{bmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \\ 0 & 0 & 0 & 1 \\ 0 & 0 & 1 & 0 \end{bmatrix}$$

---

## 3. Multi-Qubit Systems & Entangled Bell States

For an $n$-qubit system, the composite state space is formed via the Kronecker tensor product ($\otimes$).

### 3.1 Tensor Product Example
For two qubits $|a\rangle = \begin{bmatrix} a_0 \\ a_1 \end{bmatrix}$ and $|b\rangle = \begin{bmatrix} b_0 \\ b_1 \end{bmatrix}$:

$$|a\rangle \otimes |b\rangle = |ab\rangle = \begin{bmatrix} a_0 b_0 \\ a_0 b_1 \\ a_1 b_0 \\ a_1 b_1 \end{bmatrix}$$

### 3.2 The Four Maximally Entangled Bell States
The four Bell states form an orthonormal basis for a 2-qubit system:

$$|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle) = \frac{1}{\sqrt{2}} \begin{bmatrix} 1 \\ 0 \\ 0 \\ 1 \end{bmatrix}$$

$$|\Phi^-\rangle = \frac{1}{\sqrt{2}}(|00\rangle - |11\rangle) = \frac{1}{\sqrt{2}} \begin{bmatrix} 1 \\ 0 \\ 0 \\ -1 \end{bmatrix}$$

$$|\Psi^+\rangle = \frac{1}{\sqrt{2}}(|01\rangle + |10\rangle) = \frac{1}{\sqrt{2}} \begin{bmatrix} 0 \\ 1 \\ 1 \\ 0 \end{bmatrix}$$

$$|\Psi^-\rangle = \frac{1}{\sqrt{2}}(|01\rangle - |10\rangle) = \frac{1}{\sqrt{2}} \begin{bmatrix} 0 \\ 1 \\ -1 \\ 0 \end{bmatrix}$$

---

## 4. Quantum Teleportation Mathematical Workflow

Let Alice hold an arbitrary unknown signature state $|\psi\rangle_S = \alpha|0\rangle_S + \beta|1\rangle_S$.  
Alice and Bob share an entangled Bell pair $|\Phi^+\rangle_{AB} = \frac{1}{\sqrt{2}}(|00\rangle_{AB} + |11\rangle_{AB})$.

The initial 3-qubit state $|\Psi_0\rangle$ (where Qubit $S$ belongs to Alice's signature, Qubit $A$ belongs to Alice's Bell pair, and Qubit $B$ belongs to Bob's Bell pair) is:

$$|\Psi_0\rangle = |\psi\rangle_S \otimes |\Phi^+\rangle_{AB} = \frac{1}{\sqrt{2}} \left( \alpha|0\rangle_S (|00\rangle_{AB} + |11\rangle_{AB}) + \beta|1\rangle_S (|00\rangle_{AB} + |11\rangle_{AB}) \right)$$

### Step 1: Alice Applies $CNOT_{S,A}$
Alice applies a CNOT gate with qubit $S$ as control and qubit $A$ as target:

$$|\Psi_1\rangle = (CNOT_{S,A} \otimes I_B) |\Psi_0\rangle = \frac{1}{\sqrt{2}} \left( \alpha|000\rangle_{SAB} + \alpha|011\rangle_{SAB} + \beta|110\rangle_{SAB} + \beta|101\rangle_{SAB} \right)$$

### Step 2: Alice Applies Hadamard $H_S$
Alice applies a Hadamard gate to qubit $S$:

$$|\Psi_2\rangle = (H_S \otimes I_A \otimes I_B) |\Psi_1\rangle$$

Expanding this into Alice's measurement basis $(S, A)$ and Bob's qubit $B$:

$$|\Psi_2\rangle = \frac{1}{2} \left[ |00\rangle_{SA} (\alpha|0\rangle_B + \beta|1\rangle_B) + |01\rangle_{SA} (\alpha|1\rangle_B + \beta|0\rangle_B) + |10\rangle_{SA} (\alpha|0\rangle_B - \beta|1\rangle_B) + |11\rangle_{SA} (\alpha|1\rangle_B - \beta|0\rangle_B) \right]$$

### Step 3: Alice Measures Qubits $(S, A)$
Alice performs projective measurements on her two qubits, yielding two classical bits $m_1 m_2 \in \{00, 01, 10, 11\}$ with equal probability $P(m_1 m_2) = \frac{1}{4} = 25\%$.

### Step 4: Bob Applies Pauli Correction
Upon receiving $m_1 m_2$ via a classical channel, Bob applies the designated unitary Pauli correction matrix $U_B$:

| Classical Measurement $m_1 m_2$ | Bob's State Before Correction | Bob's Pauli Correction $U_B$ | Bob's Final State |
| :---: | :---: | :---: | :---: |
| **00** | $\alpha\|0\rangle + \beta\|1\rangle$ | $I = \begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix}$ | $\alpha\|0\rangle + \beta\|1\rangle = \|\psi\rangle$ |
| **01** | $\alpha\|1\rangle + \beta\|0\rangle$ | $X = \begin{bmatrix} 0 & 1 \\ 1 & 0 \end{bmatrix}$ | $\alpha\|0\rangle + \beta\|1\rangle = \|\psi\rangle$ |
| **10** | $\alpha\|0\rangle - \beta\|1\rangle$ | $Z = \begin{bmatrix} 1 & 0 \\ 0 & -1 \end{bmatrix}$ | $\alpha\|0\rangle + \beta\|1\rangle = \|\psi\rangle$ |
| **11** | $\alpha\|1\rangle - \beta\|0\rangle$ | $X Z = \begin{bmatrix} 0 & -1 \\ 1 & 0 \end{bmatrix}$ | $\alpha\|0\rangle + \beta\|1\rangle = \|\psi\rangle$ |

---

## 5. Projective Measurement & State Fidelity Math

### 5.1 Projective Measurement Operators
Projective measurement in the computational basis is defined by projection operators:

$$M_0 = |0\rangle\langle 0| = \begin{bmatrix} 1 & 0 \\ 0 & 0 \end{bmatrix}, \quad M_1 = |1\rangle\langle 1| = \begin{bmatrix} 0 & 0 \\ 0 & 1 \end{bmatrix}$$

The probability of observing outcome $m \in \{0, 1\}$ for state $|\phi\rangle$ is:

$$P(m) = \langle \phi | M_m^\dagger M_m | \phi \rangle = \langle \phi | M_m | \phi \rangle$$

### 5.2 Quantum State Fidelity ($F$)
To quantify the fidelity between the original signature state $|\psi_{exp}\rangle$ and Bob's reconstructed state $|\psi_{obs}\rangle$:

$$F(|\psi_{exp}\rangle, |\psi_{obs}\rangle) = \left| \langle \psi_{exp} | \psi_{obs} \rangle \right|^2$$

* For an ideal quantum channel with zero eavesdropping or noise: $F = 1.0$.
* For a noisy channel or under active forgery attack: $F < 1.0$.
