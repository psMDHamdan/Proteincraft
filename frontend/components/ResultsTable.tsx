"use client";

import { RankedSequence } from "@/lib/api";

export default function ResultsTable({ sequences }: { sequences: RankedSequence[] }) {
  return (
    <div className="glass rounded-xl overflow-hidden border-glow">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-slate-400 uppercase bg-surface-800/50 border-b border-surface-700">
            <tr>
              <th className="px-6 py-4 font-medium">Rank</th>
              <th className="px-6 py-4 font-medium">Sequence</th>
              <th className="px-6 py-4 font-medium">Mutations</th>
              <th className="px-6 py-4 font-medium text-right">ESM Score</th>
              <th className="px-6 py-4 font-medium text-right">Stability</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-800/50">
            {sequences.map((seq, idx) => (
              <tr key={idx} className="table-row-hover">
                <td className="px-6 py-4 font-semibold text-brand-400">#{seq.rank}</td>
                <td className="px-6 py-4 seq-mono text-slate-300 w-[400px]">
                  <div className="truncate w-[350px]">{seq.sequence}</div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1">
                    {seq.mutations_from_input.length > 0 ? (
                      seq.mutations_from_input.map((m, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 rounded bg-brand-500/10 text-brand-300 border border-brand-500/20 font-mono">
                          {m}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-500 italic">WT</span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 text-right font-mono text-slate-300">
                  {seq.esm_score.toFixed(3)}
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="w-16 h-1.5 bg-surface-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-emerald-500" 
                        style={{ width: `${Math.min(100, Math.max(0, seq.stability_proxy * 100))}%` }}
                      />
                    </div>
                    <span className="font-mono text-slate-300">{seq.stability_proxy.toFixed(2)}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
