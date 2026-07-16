"use client"

import { Search, Command } from "lucide-react"
import DatasetSelector from "./DatasetSelector"
import UploadDatasetButton from "./UploadDatasetButton"
import ApiKeyInput from "./ApiKeyInput"

export default function TopBar() {
  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-hairline bg-canvas/80 px-6 backdrop-blur-md">
      <div className="flex flex-1 items-center gap-4">
        <button className="flex items-center gap-2 rounded-[var(--radius-md)] border border-hairline bg-surface px-3 py-1.5 text-body-sm text-mute hover:bg-surface-elevated hover:text-body transition-colors">
          <Search className="h-4 w-4" />
          <span>Search workspaces...</span>
          <div className="ml-4 flex items-center gap-1 rounded bg-surface-card px-1.5 py-0.5 text-caption-sm shadow-sm">
            <Command className="h-3 w-3" />
            <span>K</span>
          </div>
        </button>
      </div>
      <div className="flex items-center gap-3">
        <UploadDatasetButton />
        <DatasetSelector />
        <ApiKeyInput />
      </div>
    </header>
  )
}
