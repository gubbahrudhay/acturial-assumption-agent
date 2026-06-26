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
        className={`h-10 w-10 rounded-full border border-[#dddddd] flex items-center justify-center hover:shadow-md transition-shadow ${apiKey ? "text-[#008a05]" : "text-[#6a6a6a]"}`}
        title="Set Gemini API Key"
      >
        <KeyRound className="h-4 w-4" />
      </button>

      {showInput && (
        <div className="absolute right-0 top-12 mt-2 w-72 bg-white border border-[#dddddd] shadow-lg rounded-xl p-4 z-50">
          <label className="block text-sm font-semibold text-[#222222] mb-2">Gemini API Key</label>
          <input 
            type="password"
            value={apiKey}
            onChange={handleSave}
            placeholder="AIza..."
            className="w-full text-sm border border-[#dddddd] rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-[#ff385c]/20 transition-all"
          />
          <p className="text-xs text-[#6a6a6a] mt-2 leading-relaxed">
            Your key is stored locally in your browser. It is securely passed to the backend agent when generating reports.
          </p>
        </div>
      )}
    </div>
  )
}
