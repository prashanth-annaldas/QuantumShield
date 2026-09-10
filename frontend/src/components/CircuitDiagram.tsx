import React from 'react';
import { ArrowRight, CheckCircle2, Radio, Key, Cpu } from 'lucide-react';

interface CircuitDiagramProps {
  classicalBits?: number[];
  fidelity?: number;
  bellPairCount?: number;
  className?: string;
}

export const CircuitDiagram: React.FC<CircuitDiagramProps> = ({
  classicalBits = [0, 1],
  fidelity = 1.0,
  bellPairCount = 256,
  className = '',
}) => {
  const m1 = classicalBits[0] ?? 0;
  const m2 = classicalBits[1] ?? 1;

  // Determine Pauli correction formula based on m1, m2
  const pauliGate = m1 === 0 && m2 === 0 ? 'I' : m1 === 0 && m2 === 1 ? 'X' : m1 === 1 && m2 === 0 ? 'Z' : 'XZ';

  return (
    <div className={`p-6 bg-white rounded-xl border border-slate-200 shadow-sm ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Teleportation Protocol Engine
            </span>
            <span className="text-xs text-slate-500 font-mono">
              256-Qubit Signature Sequence
            </span>
          </div>
          <h3 className="mt-1 text-base font-bold text-slate-900">
            Alice-to-Bob Quantum Teleportation Channel
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <div className="text-right">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">
              Teleportation Fidelity
            </span>
            <span className="text-sm font-bold font-mono text-emerald-600">
              {(fidelity * 100).toFixed(2)}% (F = {fidelity.toFixed(4)})
            </span>
          </div>
        </div>
      </div>

      {/* Scientific Circuit Stages Diagram */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-5 gap-3 relative">
        {/* Stage 1: Input & Bell State */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
          <div className="flex items-center gap-2 text-indigo-700 font-bold text-xs">
            <span>STAGE 1: INPUT & EPR</span>
          </div>
          <div className="p-2.5 bg-white rounded-lg border border-slate-200 font-mono text-xs space-y-1">
            <div className="text-slate-500">|ψ⟩ = α|0⟩ + β|1⟩</div>
            <div className="text-purple-600 font-semibold text-[11px]">|Φ⁺⟩ = (|00⟩+|11⟩)/√2</div>
          </div>
          <p className="text-[11px] text-slate-500">
            Alice encodes 256 signature states from SHA-256 digest & distributes Bell pairs.
          </p>
        </div>

        {/* Stage 2: Alice CNOT & Hadamard */}
        <div className="p-4 rounded-xl bg-purple-50/50 border border-purple-200 space-y-2">
          <div className="flex items-center gap-2 text-purple-700 font-bold text-xs">
            <span>STAGE 2: ALICE OPS</span>
          </div>
          <div className="p-2.5 bg-white rounded-lg border border-purple-200 font-mono text-xs space-y-1">
            <div className="flex justify-between items-center text-slate-700">
              <span>1. Gate:</span>
              <span className="px-1.5 py-0.5 bg-purple-100 text-purple-800 rounded font-bold">CNOT</span>
            </div>
            <div className="flex justify-between items-center text-slate-700">
              <span>2. Gate:</span>
              <span className="px-1.5 py-0.5 bg-indigo-100 text-indigo-800 rounded font-bold">Hadamard (H)</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-500">
            Alice entangles signature qubit with Bell qubit and projects state into Bell basis.
          </p>
        </div>

        {/* Stage 3: Bell Measurement */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
          <div className="flex items-center gap-2 text-indigo-700 font-bold text-xs">
            <span>STAGE 3: MEASURE</span>
          </div>
          <div className="p-2.5 bg-white rounded-lg border border-slate-200 font-mono text-xs space-y-1">
            <div className="flex justify-between items-center">
              <span className="text-slate-500">Bit m₁:</span>
              <span className="font-bold text-indigo-700">{m1}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-500">Bit m₂:</span>
              <span className="font-bold text-indigo-700">{m2}</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-500">
            Projective Z measurement yields two classical bits (m₁, m₂) collapsing local qubits.
          </p>
        </div>

        {/* Stage 4: Classical Channel */}
        <div className="p-4 rounded-xl bg-cyan-50/50 border border-cyan-200 space-y-2">
          <div className="flex items-center gap-2 text-cyan-800 font-bold text-xs">
            <span>STAGE 4: CHANNEL</span>
          </div>
          <div className="p-2.5 bg-white rounded-lg border border-cyan-200 font-mono text-xs space-y-1">
            <div className="text-slate-500 text-[11px]">Classical Channel:</div>
            <div className="text-cyan-700 font-bold">{`{ m₁: ${m1}, m₂: ${m2} }`}</div>
          </div>
          <p className="text-[11px] text-slate-500">
            Classical transmission of 256 bit-pairs ({bellPairCount * 2} bits) to Bob.
          </p>
        </div>

        {/* Stage 5: Bob Pauli Correction */}
        <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-200 space-y-2">
          <div className="flex items-center gap-2 text-emerald-800 font-bold text-xs">
            <span>STAGE 5: BOB PAULI</span>
          </div>
          <div className="p-2.5 bg-white rounded-lg border border-emerald-200 font-mono text-xs space-y-1">
            <div className="text-slate-500 text-[11px]">Correction Op:</div>
            <div className="text-emerald-700 font-bold text-sm">
              X^{m2} Z^{m1} = {pauliGate}
            </div>
          </div>
          <p className="text-[11px] text-slate-500">
            Bob applies unitary Pauli correction recovering pristine signature state |ψ⟩.
          </p>
        </div>
      </div>

      {/* Protocol Summary Metrics */}
      <div className="mt-5 p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-600">
        <div>
          <span className="text-slate-400">Bell Pairs Distributed:</span>{' '}
          <span className="font-bold text-slate-800">{bellPairCount} pairs</span>
        </div>
        <div>
          <span className="text-slate-400">Classical Transmission:</span>{' '}
          <span className="font-bold text-slate-800">{bellPairCount * 2} classical bits</span>
        </div>
        <div>
          <span className="text-slate-400">Mathematical No-Cloning Theorem:</span>{' '}
          <span className="font-bold text-indigo-700">Satisfied (State Transferred, Not Duplicated)</span>
        </div>
      </div>
    </div>
  );
};
