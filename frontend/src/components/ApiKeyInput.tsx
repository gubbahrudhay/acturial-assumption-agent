"use client"

import { useState, useEffect } from "react"
import { KeyRound } from "lucide-react"

export default function ApiKeyInput() {
  const [apiKey, setApiKey] = useState("")
  const [showInput, setShowInput] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem("gemini_api_key")
    if (saved) setApiKey(saved)
  }, [])

  const handleSave = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setApiKey(val)
    localStorage.setItem("gemini_api_key", val)
  }

  return (
    <div className="relative flex items-center">
      <button 
        onClick={() => setShowInput(!showInput)}
        className={`h-[36px] w-[36px] rounded-[var(--radius-md)] border border-hairline bg-surface hover:bg-surface-elevated flex items-center justify-center transition-colors ${apiKey ? "text-accent-green" : "text-mute hover:text-body"}`}
        title="Set Gemini API Key"
      >
        <KeyRound className="h-4 w-4" />
      </button>

      {showInput && (
        <div className="absolute right-0 top-12 mt-2 w-72 bg-surface-elevated border border-hairline shadow-lg rounded-[var(--radius-lg)] p-4 z-50">
          <label className="block text-body-sm-strong text-ink mb-2">Gemini API Key</label>
          <input 
            type="password"
            value={apiKey}
            onChange={handleSave}
            placeholder="AIza..."
            className="w-full text-body-sm bg-surface border border-hairline rounded-[var(--radius-md)] px-3 py-2 outline-none focus:ring-2 focus:ring-white/20 transition-all text-body placeholder:text-mute"
          />
          <p className="text-caption-sm text-mute mt-2 leading-relaxed">
            Your key is stored locally in your browser. It is securely passed to the backend agent when generating reports.
          </p>
        </div>
      )}
    </div>
  )
}
