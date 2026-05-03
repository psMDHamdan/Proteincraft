"use client";

import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';

SyntaxHighlighter.registerLanguage('json', json);

export default function JsonViewer({ data }: { data: any }) {
  return (
    <div className="glass rounded-xl overflow-hidden text-sm">
      <div className="bg-surface-800/80 px-4 py-2 border-b border-surface-700 flex justify-between items-center">
        <span className="text-xs font-mono text-slate-400">raw_response.json</span>
      </div>
      <SyntaxHighlighter 
        language="json" 
        style={atomOneDark}
        customStyle={{ margin: 0, padding: '1rem', background: 'transparent' }}
        wrapLines={true}
      >
        {JSON.stringify(data, null, 2)}
      </SyntaxHighlighter>
    </div>
  );
}
