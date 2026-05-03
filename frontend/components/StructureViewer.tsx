"use client";

import { useEffect, useRef, useState } from "react";

// Minimal wrapper for Mol* using their embedded CDN version
export default function StructureViewer({ pdbString }: { pdbString: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let scriptEl: HTMLScriptElement | null = null;
    let linkEl: HTMLLinkElement | null = null;

    const initViewer = async () => {
      try {
        if (!containerRef.current) return;
        
        // Dynamic loading of Mol* CSS
        linkEl = document.createElement("link");
        linkEl.rel = "stylesheet";
        linkEl.href = "https://cdn.jsdelivr.net/npm/molstar@3.39.0/build/viewer/molstar.css";
        document.head.appendChild(linkEl);

        // Dynamic loading of Mol* JS
        scriptEl = document.createElement("script");
        scriptEl.src = "https://cdn.jsdelivr.net/npm/molstar@3.39.0/build/viewer/molstar.js";
        scriptEl.onload = () => {
          if ((window as any).molstar) {
            const plugin = new (window as any).molstar.Viewer(containerRef.current, {
              layoutIsExpanded: false,
              layoutShowControls: false,
              layoutShowRemoteState: false,
              layoutShowSequence: true,
              layoutShowLog: false,
              layoutShowLeftPanel: true,
            });
            
            // Load PDB string directly
            plugin.loadStructureFromData(pdbString, 'pdb', { dataLabel: 'Predicted Structure' });
          }
        };
        document.head.appendChild(scriptEl);

      } catch (e) {
        console.error(e);
        setError(true);
      }
    };

    initViewer();

    return () => {
      if (linkEl) document.head.removeChild(linkEl);
      if (scriptEl) document.head.removeChild(scriptEl);
    };
  }, [pdbString]);

  if (error) {
    return <div className="p-4 bg-red-900/20 text-red-400 rounded text-sm border border-red-500/20">Failed to load Mol* viewer.</div>;
  }

  return (
    <div className="w-full h-[500px] rounded-xl overflow-hidden glass relative border border-surface-700">
      <div className="absolute inset-0 z-0 bg-[#111111]" ref={containerRef} />
    </div>
  );
}
