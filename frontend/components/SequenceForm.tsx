"use client";

import { useState } from "react";
import * as Tabs from "@radix-ui/react-tabs";
import { UploadCloud, Sparkles } from "lucide-react";
import toast from "react-hot-toast";

interface SequenceFormProps {
  onSubmit: (data: any) => Promise<void>;
  isLoading: boolean;
}

export default function SequenceForm({ onSubmit, isLoading }: SequenceFormProps) {
  const [activeTab, setActiveTab] = useState("sequence");
  const [sequence, setSequence] = useState("");
  const [fasta, setFasta] = useState("");
  const [targetAntigen, setTargetAntigen] = useState("");
  const [desiredFunction, setDesiredFunction] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (activeTab === "sequence" && !sequence.trim()) {
      toast.error("Please enter a sequence");
      return;
    }
    if (activeTab === "fasta" && !fasta.trim()) {
      toast.error("Please provide FASTA content");
      return;
    }

    const reqData: any = {
      target_antigen: targetAntigen || undefined,
      desired_function: desiredFunction || undefined,
      top_k: 5,
    };

    if (activeTab === "sequence") {
      reqData.sequence = sequence.trim().toUpperCase();
    } else {
      reqData.fasta_content = fasta.trim();
    }

    await onSubmit(reqData);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const result = event.target?.result;
      if (typeof result === "string") {
        setFasta(result);
        toast.success("FASTA file loaded");
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="glass rounded-2xl p-1 border-glow shadow-card relative z-10 animate-fade-in">
      <div className="bg-surface-900 rounded-xl p-6 sm:p-8">
        <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
          <Tabs.List className="flex gap-2 p-1 bg-surface-800 rounded-lg mb-8">
            <Tabs.Trigger
              value="sequence"
              className="flex-1 py-2.5 text-sm font-medium rounded-md text-slate-400 hover:text-white data-[state=active]:bg-brand-500/20 data-[state=active]:text-brand-400 transition-all"
            >
              Raw Sequence
            </Tabs.Trigger>
            <Tabs.Trigger
              value="fasta"
              className="flex-1 py-2.5 text-sm font-medium rounded-md text-slate-400 hover:text-white data-[state=active]:bg-brand-500/20 data-[state=active]:text-brand-400 transition-all"
            >
              FASTA Upload
            </Tabs.Trigger>
          </Tabs.List>

          <form onSubmit={handleSubmit} className="space-y-6">
            <Tabs.Content value="sequence" className="space-y-4 animate-fade-in">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Input Amino Acid Sequence
                </label>
                <textarea
                  value={sequence}
                  onChange={(e) => setSequence(e.target.value)}
                  placeholder="e.g. EVQLVESGGGLVQPGGSLRLSCAAS..."
                  className="w-full h-32 p-4 input-glow font-mono text-sm resize-none"
                  spellCheck={false}
                />
              </div>
            </Tabs.Content>

            <Tabs.Content value="fasta" className="space-y-4 animate-fade-in">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  FASTA Content
                </label>
                <div className="relative">
                  <textarea
                    value={fasta}
                    onChange={(e) => setFasta(e.target.value)}
                    placeholder=">protein_name&#10;SEQUENCE..."
                    className="w-full h-32 p-4 pb-12 input-glow font-mono text-sm resize-none"
                    spellCheck={false}
                  />
                  <div className="absolute bottom-3 right-3">
                    <label className="cursor-pointer inline-flex items-center gap-2 px-3 py-1.5 bg-surface-700 hover:bg-surface-600 border border-surface-500 rounded-md text-xs font-medium text-slate-200 transition-colors">
                      <UploadCloud size={14} />
                      Upload File
                      <input type="file" accept=".fasta,.fa,.txt" className="hidden" onChange={handleFileUpload} />
                    </label>
                  </div>
                </div>
              </div>
            </Tabs.Content>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 border-t border-white/5">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Target Antigen Context (Optional)
                </label>
                <input
                  type="text"
                  value={targetAntigen}
                  onChange={(e) => setTargetAntigen(e.target.value)}
                  placeholder="Antigen sequence..."
                  className="w-full p-3 input-glow text-sm font-mono"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Desired Function (Optional)
                </label>
                <input
                  type="text"
                  value={desiredFunction}
                  onChange={(e) => setDesiredFunction(e.target.value)}
                  placeholder="e.g. Improve thermostability..."
                  className="w-full p-3 input-glow text-sm"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 px-6 rounded-lg font-semibold text-white transition-all
                bg-brand-600 hover:bg-brand-500 hover:shadow-glow-md disabled:opacity-50 disabled:cursor-not-allowed
                flex items-center justify-center gap-2 relative overflow-hidden group"
            >
              {isLoading ? (
                <>
                  <div className="spinner" />
                  <span>Engineering sequence...</span>
                </>
              ) : (
                <>
                  <Sparkles size={18} className="text-emerald-300 group-hover:animate-pulse" />
                  <span>Generate Designs</span>
                </>
              )}
            </button>
          </form>
        </Tabs.Root>
      </div>
    </div>
  );
}
