"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import SequenceForm from "@/components/SequenceForm";
import { api } from "@/lib/api";
import toast from "react-hot-toast";

export default function Home() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleDesign = async (data: any) => {
    setIsLoading(true);
    const toastId = toast.loading("Initializing AI pipeline...");
    try {
      const response = await api.designSequence(data);
      toast.success("Designs generated successfully!", { id: toastId });
      router.push(`/results/${response.job_id}`);
    } catch (err: any) {
      toast.error(err.message || "Failed to design sequence", { id: toastId });
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col relative">
      <div className="flex-grow flex flex-col items-center justify-center px-4 py-20 relative z-10">
        
        {/* Hero Text */}
        <div className="text-center max-w-3xl mb-12 animate-slide-up">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-semibold tracking-wider mb-6">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-500"></span>
            </span>
            ESM2 + GEMINI 2.5
          </div>
          <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight mb-6">
            Engineer better proteins <br />
            <span className="gradient-text">with AI reasoning</span>
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Upload your sequence to generate optimized variants. ProteinCraft uses ESM2 for masked language modeling and Gemini for deep biophysical reasoning to rank candidates.
          </p>
        </div>

        {/* Input Form */}
        <div className="w-full max-w-4xl mx-auto">
          <SequenceForm onSubmit={handleDesign} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
}
