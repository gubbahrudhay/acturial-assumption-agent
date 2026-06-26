"use client"

import { useRef, useState } from "react"
import axios from "axios"
import { Upload } from "lucide-react"

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
      await axios.post("http://localhost:8000/api/upload", formData)
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
        className="text-[13px] font-bold tracking-wide text-[#222222] hover:bg-[#f7f7f7] px-4 py-2 rounded-full transition-colors hidden sm:flex items-center gap-2 uppercase disabled:opacity-50"
      >
        <Upload className="h-4 w-4" />
        {isUploading ? "Uploading..." : "Upload Dataset"}
      </button>
    </>
  )
}
