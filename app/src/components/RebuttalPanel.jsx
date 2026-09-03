import { useState } from 'react'
import { Check, Copy } from 'lucide-react'

export default function RebuttalPanel({ text }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // clipboard access can be denied (permissions, insecure context) — nothing else to do
    }
  }

  return (
    <div className="border border-line bg-surface p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-ink">Rebuttal draft</h2>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 border border-line px-2.5 py-1.5 text-sm text-ink hover:bg-canvas focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger"
        >
          {copied ? (
            <Check className="h-3.5 w-3.5 text-contest" aria-hidden="true" />
          ) : (
            <Copy className="h-3.5 w-3.5" aria-hidden="true" />
          )}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="mt-4 max-h-96 overflow-y-auto whitespace-pre-wrap border border-line bg-canvas p-3 font-mono text-[13px] leading-relaxed text-ink">
        {text}
      </pre>
      <p className="mt-3 border border-line bg-canvas p-3 text-sm text-slate">
        Drafted from records on file. No evidence is generated. Review before submitting.
      </p>
    </div>
  )
}
