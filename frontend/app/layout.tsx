import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "ProteinCraft — Engineer Better Proteins with AI",
  description:
    "AI-powered protein engineering platform. Design, optimize, and predict protein structures using ESM2 embeddings, Gemini reasoning, and ESMFold structure prediction.",
  keywords: ["protein engineering", "AI", "ESM2", "protein design", "bioinformatics", "ESMFold"],
  authors: [{ name: "ProteinCraft" }],
  openGraph: {
    title: "ProteinCraft",
    description: "Engineer better proteins with AI",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="min-h-screen bg-[#0a0f1e] text-slate-100 antialiased">
        {/* Global background glow orbs */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
          <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-brand-600/10 blur-[120px]" />
          <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-emerald-600/8 blur-[100px]" />
          <div className="absolute top-[40%] left-[50%] -translate-x-1/2 w-[400px] h-[400px] rounded-full bg-brand-900/20 blur-[80px]" />
        </div>

        <nav className="sticky top-0 z-50 border-b border-white/5 glass">
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-400 to-emerald-400 flex items-center justify-center shadow-glow-sm">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="text-white">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" fill="currentColor"/>
                </svg>
              </div>
              <span className="text-lg font-bold gradient-text">ProteinCraft</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-slate-400">
              <a href="/" className="hover:text-brand-400 transition-colors">Design</a>
              <a href="/docs" target="_blank" rel="noopener noreferrer" className="hover:text-brand-400 transition-colors">API Docs</a>
              <a
                href="https://github.com/proteincraft/proteincraft"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 hover:text-brand-400 transition-colors"
              >
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z"/>
                </svg>
                GitHub
              </a>
            </div>
          </div>
        </nav>

        <main>{children}</main>

        <footer className="mt-24 border-t border-white/5 py-10 text-center text-sm text-slate-500">
          <p>
            ProteinCraft · Powered by{" "}
            <span className="text-brand-400">ESM2</span>,{" "}
            <span className="text-emerald-400">Gemini</span>, and{" "}
            <span className="text-brand-400">ESMFold</span>
          </p>
        </footer>

        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: "#1e293b",
              color: "#e2e8f0",
              border: "1px solid rgba(14,165,233,0.2)",
            },
          }}
        />
      </body>
    </html>
  );
}
