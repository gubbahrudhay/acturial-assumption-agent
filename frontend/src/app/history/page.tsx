"use client"

import React, { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { PlayCircle, Clock, Search, ChevronRight, Activity, Target, AlertCircle, RefreshCw } from "lucide-react"
import { EnterpriseCard } from "@/components/ui/EnterpriseCard"
import { Badge } from "@/components/ui/badge"
import { API_BASE_URL } from "@/lib/api"

export default function HistoryWorkspace() {
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")

  const fetchHistory = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await fetch(`${API_BASE_URL}/api/investigations`)
      if (!res.ok) throw new Error(`Status ${res.status}`)
      const data = await res.json()
      // Normalize backend data
      const investigations = Array.isArray(data) ? data : (data.investigations || [])
      setHistory(investigations)
    } catch (err: any) {
      setError("Failed to load investigation history. Please ensure backend is running.")
      setHistory([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchHistory() }, [])

  const filtered = history.filter(h =>
    h.id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    h.dataset?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="flex flex-col min-h-screen p-6 md:p-8 lg:p-10">
      <div className="w-full max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-10 gap-4">
          <div>
            <motion.h1 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-display-lg text-ink tracking-tight"
            >
              Investigation History
            </motion.h1>
            <motion.p 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.05 }}
              className="text-body-lg text-mute mt-2"
            >
              Audit and replay past AI investigations to understand deterministic traces.
            </motion.p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-mute" />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search by ID or dataset..."
                aria-label="Search investigations"
                className="pl-9 pr-4 py-2 border border-hairline rounded-[var(--radius-md)] text-body-sm bg-surface focus:outline-none focus:ring-2 focus:ring-accent-blue/30 w-64 text-body placeholder:text-mute transition-colors"
              />
            </div>
            <button
              onClick={fetchHistory}
              className="p-2 border border-hairline rounded-[var(--radius-md)] bg-surface text-mute hover:bg-surface-elevated hover:text-body transition-colors"
              aria-label="Refresh history"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 gap-3">
          {loading ? (
            // Skeleton loaders
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-[88px] skeleton rounded-[var(--radius-xl)]" />
            ))
          ) : error ? (
            <EnterpriseCard>
              <div className="flex flex-col items-center justify-center p-12 text-center gap-3">
                <AlertCircle className="h-8 w-8 text-accent-red" />
                <p className="text-body-sm text-mute">{error}</p>
                <button onClick={fetchHistory} className="text-accent-blue text-body-sm-strong hover:underline">Retry</button>
              </div>
            </EnterpriseCard>
          ) : filtered.length === 0 ? (
            <EnterpriseCard>
              <div className="flex flex-col items-center justify-center p-12 text-center gap-2">
                <Search className="h-8 w-8 text-ash" />
                <p className="text-body-sm text-mute">{searchQuery ? "No investigations match your search." : "No investigation history yet. Run an investigation to get started."}</p>
              </div>
            </EnterpriseCard>
          ) : (
            filtered.map((run, idx) => (
              <motion.div
                key={run.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.03 }}
              >
                <EnterpriseCard className="hover:bg-surface-elevated transition-colors cursor-pointer group">
                  <div className="flex flex-col md:flex-row justify-between px-5 py-4 items-start md:items-center gap-3">
                    
                    <div className="flex items-center gap-4">
                      <div className={`p-2.5 rounded-[var(--radius-md)] ${run.severity === 'High' ? 'bg-accent-red-soft text-accent-red' : run.severity === 'Medium' ? 'bg-accent-yellow-soft text-accent-yellow' : 'bg-accent-green-soft text-accent-green'}`}>
                        <Activity className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="text-body-sm-strong text-ink flex items-center gap-2">
                          <span className="font-mono text-[10px] bg-surface-elevated border border-hairline px-1.5 py-0.5 rounded-[var(--radius-xs)] text-mute uppercase">{run.id}</span>
                          {run.dataset}
                        </h3>
                        <div className="flex items-center gap-3 text-caption-sm text-ash mt-1">
                          <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {run.date}</span>
                          <span className="w-1 h-1 rounded-full bg-hairline-strong" />
                          <span className="flex items-center gap-1"><Target className="w-3 h-3" /> {run.triggers?.join(", ")}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 w-full md:w-auto justify-between md:justify-end">
                      <Badge className={`shadow-none border ${run.status === 'Completed' ? 'bg-accent-green-soft text-accent-green border-accent-green-soft' : 'bg-surface text-mute border-hairline'}`}>
                        {run.status}
                      </Badge>
                      
                      <button className="flex items-center gap-1.5 text-accent-blue text-body-sm-strong opacity-0 group-hover:opacity-100 transition-opacity px-3 py-1.5 rounded-[var(--radius-md)] hover:bg-accent-blue-soft">
                        <PlayCircle className="w-4 h-4" /> Replay <ChevronRight className="w-3 h-3 opacity-50" />
                      </button>
                    </div>
                    
                  </div>
                </EnterpriseCard>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
