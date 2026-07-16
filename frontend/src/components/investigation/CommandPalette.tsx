import React, { useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Search, Play, BarChart3, MessageSquare, FileText } from "lucide-react"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"

export default function CommandPalette({ isOpen, setIsOpen, runInvestigation, downloadPdf, openCopilot }: any) {
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setIsOpen((open: boolean) => !open)
      }
    }
    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [setIsOpen])

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-canvas/40 backdrop-blur-sm" onClick={() => setIsOpen(false)}>
          <motion.div 
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            onClick={e => e.stopPropagation()}
            className="bg-surface-elevated w-full max-w-2xl rounded-[var(--radius-xl)] shadow-2xl overflow-hidden border border-hairline-strong"
          >
            <div className="flex items-center px-4 py-3 border-b border-hairline">
              <Search className="h-5 w-5 text-mute mr-3" />
              <input 
                autoFocus
                placeholder="Search investigations, reports, actions..." 
                className="flex-1 bg-transparent text-ink placeholder:text-mute outline-none text-body-lg"
              />
              <Badge className="bg-surface text-mute font-mono shadow-none hover:bg-surface border-hairline uppercase">ESC</Badge>
            </div>
            <div className="p-2">
              <div className="px-3 py-2 text-caption-sm font-semibold text-ash uppercase tracking-wider">Actions</div>
              <button onClick={() => {runInvestigation(); setIsOpen(false)}} className="w-full text-left px-3 py-3 rounded-[var(--radius-md)] hover:bg-surface flex items-center group transition-colors">
                <Play className="h-4 w-4 mr-3 text-accent-blue" />
                <span className="text-ink font-medium">Run Full Investigation</span>
              </button>
              <Link href="/analytics" onClick={() => setIsOpen(false)} className="w-full text-left px-3 py-3 rounded-[var(--radius-md)] hover:bg-surface flex items-center group transition-colors">
                <BarChart3 className="h-4 w-4 mr-3 text-accent-green" />
                <span className="text-ink font-medium">View Analytics Dashboard</span>
              </Link>
              <button onClick={() => {openCopilot(); setIsOpen(false)}} className="w-full text-left px-3 py-3 rounded-[var(--radius-md)] hover:bg-surface flex items-center group transition-colors">
                <MessageSquare className="h-4 w-4 mr-3 text-accent-yellow" />
                <span className="text-ink font-medium">Open AI Copilot</span>
              </button>
              <button onClick={() => {downloadPdf(); setIsOpen(false)}} className="w-full text-left px-3 py-3 rounded-[var(--radius-md)] hover:bg-surface flex items-center group transition-colors">
                <FileText className="h-4 w-4 mr-3 text-ash" />
                <span className="text-ink font-medium">Export Report to PDF</span>
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
