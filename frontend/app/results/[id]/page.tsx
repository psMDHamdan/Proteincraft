"use client";

import { useEffect, useState } from "react";
import { api, DesignResponse, StructureResponse } from "@/lib/api";
import ResultsTable from "@/components/ResultsTable";
import PropertyCard from "@/components/PropertyCard";
import StructureViewer from "@/components/StructureViewer";
import JsonViewer from "@/components/JsonViewer";
import { Sparkles, Activity, Dna, FileJson, AlertCircle } from "lucide-react";

export default function ResultsPage({ params }: { params: { id: string } }) {
  const [data, setData] = useState<DesignResponse | null>(null);
  const [pdbData, setPdbData] = useState<StructureResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFolding, setIsFolding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await api.getProtein(params.id) as unknown as DesignResponse;
        setData(res);
        
        // Auto-trigger folding for the best sequence
        if (res.designed_sequences && res.designed_sequences.length > 0) {
          setIsFolding(true);
          try {
            const bestSeq = res.designed_sequences[0].sequence;
            const fold = await api.predictStructure(bestSeq, res.job_id);
            setPdbData(fold);
          } catch (e) {
            console.error("Folding failed", e);
          } finally {
            setIsFolding(false);
          }
        }

      } catch (err: any) {
        setError(err.message || "Failed to load job");
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [params.id]);

  if (isLoading) {
    return (
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 animate-pulse-slow">
          <div className="w-16 h-16 border-4 border-brand-500/20 border-t-brand-500 rounded-full animate-spin-slow" />
          <p className="text-slate-400 font-mono tracking-widest text-sm uppercase">Loading results...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center">
        <div className="glass p-8 rounded-2xl text-center max-w-md">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">Job Not Found</h2>
          <p className="text-slate-400 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 space-y-12 animate-fade-in">
      
      {/* Header */}
      <div className="border-b border-white/5 pb-8">
        <div className="flex items-center gap-3 mb-2">
          <Dna className="text-brand-400" />
          <h1 className="text-3xl font-bold">Design Results</h1>
        </div>
        <p className="text-slate-400 font-mono text-sm">Job ID: {data.job_id}</p>
      </div>

      {/* Gemini Reasoning Panel */}
      <div className="glass rounded-2xl p-6 md:p-8 bg-gradient-to-r from-brand-900/10 to-emerald-900/10 border border-brand-500/20 shadow-glow-sm">
        <div className="flex gap-4">
          <div className="mt-1">
            <Sparkles className="text-emerald-400" size={24} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-200 mb-2">AI Scientist Analysis</h3>
            <p className="text-slate-300 leading-relaxed text-sm md:text-base">
              {data.gemini_explanation || "No explanation generated."}
            </p>
          </div>
        </div>
      </div>

      {/* Main Stats */}
      <div>
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
          <Activity className="text-brand-400" size={20} />
          Top Sequence Properties
        </h2>
        {data.properties ? (
          <PropertyCard properties={data.properties} />
        ) : (
          <div className="p-4 bg-surface-800 rounded-lg text-slate-400 text-sm">Properties unavailable.</div>
        )}
      </div>

      {/* Ranked Table */}
      <div>
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
          <Dna className="text-brand-400" size={20} />
          Ranked Candidates
        </h2>
        <ResultsTable sequences={data.designed_sequences} />
      </div>

      {/* 3D Structure */}
      <div>
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
          <Activity className="text-brand-400" size={20} />
          Predicted Structure (Top Rank)
        </h2>
        {isFolding ? (
          <div className="h-[500px] glass flex items-center justify-center rounded-xl border border-surface-700">
            <div className="flex flex-col items-center gap-3">
              <div className="spinner" />
              <p className="text-sm text-slate-400 font-mono">Folding with ESMFold...</p>
            </div>
          </div>
        ) : pdbData ? (
          <div className="space-y-4">
            <div className="flex items-center gap-4 text-sm bg-surface-800/50 p-3 rounded-lg border border-surface-700">
              <span className="font-semibold text-slate-300">Confidence Note:</span>
              <span className={pdbData.mean_plddt > 70 ? "text-emerald-400" : "text-amber-400"}>
                {pdbData.confidence_note}
              </span>
              <span className="ml-auto font-mono text-slate-400">Mean pLDDT: {pdbData.mean_plddt}</span>
            </div>
            <StructureViewer pdbString={pdbData.pdb_string} />
          </div>
        ) : (
          <div className="p-4 bg-surface-800 rounded-lg text-slate-400 text-sm border border-surface-700">
            Structure prediction skipped or failed.
          </div>
        )}
      </div>

      {/* Raw JSON */}
      <div>
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
          <FileJson className="text-brand-400" size={20} />
          Raw Response Data
        </h2>
        <JsonViewer data={data} />
      </div>

    </div>
  );
}
