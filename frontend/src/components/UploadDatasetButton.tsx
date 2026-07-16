"use client"

import { useRef, useState } from "react"
import axios from "axios"
import { Upload } from "lucide-react"
import { API_BASE_URL } from "@/lib/api"

export default function UploadDatasetButton() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    const formData = new FormData()
    formData.append("file", file)

    try {
      await axios.post(`${API_BASE_URL}/api/upload`, formData)
      // Refresh the page to reload datasets
      window.location.reload()
    } catch (error) {
      console.error("Error uploading file:", error)
      alert("Failed to upload dataset. Please make sure it is a valid CSV.")
    } finally {
      setIsUploading(false)
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    }
  }

  return (
    <>
      <input 
        type="file" 
        accept=".csv" 
        ref={fileInputRef} 
        onChange={handleFileChange} 
        className="hidden" 
      />
      <button 
        onClick={() => fileInputRef.current?.click()}
        disabled={isUploading}
        className="text-body-sm-strong text-ink bg-surface border border-hairline hover:bg-surface-elevated px-4 py-1.5 rounded-[var(--radius-md)] transition-colors hidden sm:flex items-center gap-2 disabled:opacity-50"
      >
        <Upload className="h-4 w-4 text-mute" />
        {isUploading ? "Uploading..." : "Upload Dataset"}
      </button>
    </>
  )
}
