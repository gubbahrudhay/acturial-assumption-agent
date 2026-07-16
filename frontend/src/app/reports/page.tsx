"use client"

import React, { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { FileText, Download, Calendar, Search, Filter, AlertCircle, RefreshCw } from "lucide-react"
import { API_BASE_URL } from "@/lib/api"
import { EnterpriseCard, EnterpriseCardHeader, EnterpriseCardTitle, EnterpriseCardContent } from "@/components/ui/EnterpriseCard"

export default function ReportsWorkspace() {
  const [reports, setReports] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")

  const fetchReports = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await fetch(`${API_BASE_URL}/api/investigations`)
      if (!res.ok) throw new Error(`Status ${res.status}`)
      const data = await res.json()
      const investigations = Array.isArray(data) ? data : (data.investigations || [])
      // Map investigations to report format
      if (investigations.length > 0) {
        setReports(investigations.map((inv: any, i: number) => ({
          id: inv.id || `REP-${String(i + 1).padStart(4, '0')}`,
          title: inv.dataset || inv.title || `Investigation Report ${i + 1}`,
          date: inv.date || inv.created_at || new Date().toISOString().split('T')[0],
          size: "—",
          type: inv.status === 'Completed' ? 'Full Investigation' : 'In Progress',
        })))
      } else {
        setReports([])
      }
    } catch {
      setError("Failed to load investigation reports.")
      setReports([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchReports() }, [])

  const filtered = reports.filter(r =>
    r.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.id?.toLowerCase().includes(searchQuery.toLowerCase())
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
              Investigation Reports
            </motion.h1>
            <motion.p 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.05 }}
              className="text-body-lg text-mute mt-2"
            >
              Access generated PDF reports, audit logs, and executive summaries.
            </motion.p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-mute" />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search reports..."
                aria-label="Search reports"
                className="pl-9 pr-4 py-2 border border-hairline rounded-[var(--radius-md)] text-body-sm bg-surface focus:outline-none focus:ring-2 focus:ring-accent-blue/30 w-56 text-body placeholder:text-mute transition-colors"
              />
            </div>
            <button
              onClick={fetchReports}
              className="p-2 border border-hairline rounded-[var(--radius-md)] bg-surface text-mute hover:bg-surface-elevated hover:text-body transition-colors"
              aria-label="Refresh reports"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Table */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <EnterpriseCard>
            <EnterpriseCardHeader>
              <EnterpriseCardTitle>Generated Documents</EnterpriseCardTitle>
            </EnterpriseCardHeader>
            <EnterpriseCardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left" role="table">
                  <thead className="text-caption-sm text-ash uppercase bg-surface-elevated border-b border-hairline">
                    <tr>
                      <th className="px-6 py-3.5 font-medium" scope="col">Report Name</th>
                      <th className="px-6 py-3.5 font-medium" scope="col">Report ID</th>
                      <th className="px-6 py-3.5 font-medium" scope="col">Type</th>
                      <th className="px-6 py-3.5 font-medium" scope="col">Date Generated</th>
                      <th className="px-6 py-3.5 font-medium text-right" scope="col">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-hairline">
                    {loading ? (
                      Array.from({ length: 4 }).map((_, i) => (
                        <tr key={i}>
                          <td className="px-6 py-4"><div className="skeleton h-4 w-48" /></td>
                          <td className="px-6 py-4"><div className="skeleton h-4 w-16" /></td>
                          <td className="px-6 py-4"><div className="skeleton h-4 w-24" /></td>
                          <td className="px-6 py-4"><div className="skeleton h-4 w-20" /></td>
                          <td className="px-6 py-4"><div className="skeleton h-4 w-16 ml-auto" /></td>
                        </tr>
                      ))
                    ) : filtered.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-6 py-12 text-center">
                          <div className="flex flex-col items-center gap-2">
                            <FileText className="h-8 w-8 text-ash" />
                            <p className="text-body-sm text-mute">{searchQuery ? "No reports match your search." : "No reports generated yet."}</p>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      filtered.map((report) => (
                        <tr key={report.id} className="hover:bg-surface-elevated transition-colors group cursor-pointer text-body-sm">
                          <td className="px-6 py-4 text-ink flex items-center gap-3">
                            <div className="p-2 bg-accent-blue-soft text-accent-blue rounded-[var(--radius-md)] shrink-0">
                              <FileText className="h-4 w-4" />
                            </div>
                            <span className="font-medium">{report.title}</span>
                          </td>
                          <td className="px-6 py-4 font-mono text-mute text-caption-sm">{report.id}</td>
                          <td className="px-6 py-4">
                            <span className="bg-surface-elevated text-ash px-2.5 py-1 rounded-[var(--radius-sm)] text-caption-sm font-medium border border-hairline">
                              {report.type}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-mute">
                            <span className="flex items-center gap-1.5">
                              <Calendar className="h-3 w-3" />
                              {report.date}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right">
                            <button className="text-accent-blue font-medium flex items-center justify-end gap-1 w-full opacity-0 group-hover:opacity-100 transition-opacity hover:underline">
                              <Download className="h-4 w-4" /> Download
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </EnterpriseCardContent>
          </EnterpriseCard>
        </motion.div>
      </div>
    </div>
  )
}
