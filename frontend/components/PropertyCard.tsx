"use client";

import { PropertyResult } from "@/lib/api";

export default function PropertyCard({ properties }: { properties: PropertyResult }) {
  
  const getInstabilityBadge = (idx: number) => {
    if (idx < 40) return <span className="badge badge-stable">Stable</span>;
    if (idx < 60) return <span className="badge badge-border">Borderline</span>;
    return <span className="badge badge-unstable">Unstable</span>;
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      
      <div className="glass rounded-xl p-5 border-l-2 border-l-emerald-500">
        <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">Instability</p>
        <div className="flex items-end justify-between">
          <span className="text-2xl font-bold font-mono">{properties.instability_index.toFixed(1)}</span>
          {getInstabilityBadge(properties.instability_index)}
        </div>
      </div>

      <div className="glass rounded-xl p-5 border-l-2 border-l-brand-500">
        <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">Isoelectric Point</p>
        <div className="flex items-end justify-between">
          <span className="text-2xl font-bold font-mono">{properties.isoelectric_point.toFixed(2)}</span>
          <span className="text-sm text-slate-500 font-mono">pH</span>
        </div>
      </div>

      <div className="glass rounded-xl p-5 border-l-2 border-l-purple-500">
        <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">Mol. Weight</p>
        <div className="flex items-end justify-between">
          <span className="text-2xl font-bold font-mono">{(properties.molecular_weight / 1000).toFixed(1)}</span>
          <span className="text-sm text-slate-500 font-mono">kDa</span>
        </div>
      </div>

      <div className="glass rounded-xl p-5 border-l-2 border-l-amber-500">
        <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">Aromaticity</p>
        <div className="flex items-end justify-between">
          <span className="text-2xl font-bold font-mono">{(properties.aromaticity * 100).toFixed(1)}</span>
          <span className="text-sm text-slate-500 font-mono">%</span>
        </div>
      </div>

    </div>
  );
}
