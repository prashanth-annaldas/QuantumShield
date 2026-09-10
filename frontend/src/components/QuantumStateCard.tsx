import React from 'react';
import { Cpu } from 'lucide-react';

interface QuantumStateCardProps {
  index: number;
  bit: number;
  amplitude0?: string;
  amplitude1?: string;
  className?: string;
}

export const QuantumStateCard: React.FC<QuantumStateCardProps> = ({
  index,
  bit,
  amplitude0 = bit === 0 ? '1.0 + 0.0i' : '0.0 + 0.0i',
  amplitude1 = bit === 1 ? '1.0 + 0.0i' : '0.0 + 0.0i',
  className = '',
}) => {
  const diracLabel = bit === 0 ? '|0⟩' : '|1⟩';
  const basis = bit === 0 ? 'Computational |0⟩' : 'Computational |1⟩';

  return (
    <div
      className={`p-3.5 bg-white rounded-xl border border-slate-200 shadow-sm hover:border-purple-300 hover:shadow-md transition-all duration-200 ${className}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Cpu className="w-3.5 h-3.5 text-purple-600" />
          <span className="text-[11px] font-mono font-semibold text-slate-500 uppercase">
            Qubit #{index.toString().padStart(3, '0')}
          </span>
        </div>
        <span className="px-2 py-0.5 text-xs font-mono font-bold bg-purple-50 text-purple-700 rounded-md border border-purple-200">
          {diracLabel}
        </span>
      </div>

      <div className="mt-2.5 p-2 bg-slate-50 rounded-lg border border-slate-100 font-mono text-[11px] space-y-1 text-slate-600">
        <div className="flex justify-between items-center">
          <span className="text-slate-400">α (|0⟩):</span>
          <span className="font-semibold text-slate-800">{amplitude0}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400">β (|1⟩):</span>
          <span className="font-semibold text-slate-800">{amplitude1}</span>
        </div>
      </div>

      <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400">
        <span>Basis: {basis}</span>
        <span>Bit Val: {bit}</span>
      </div>
    </div>
  );
};
