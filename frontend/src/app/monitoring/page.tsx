"use client"

import { useState, useEffect } from "react"
import { Activity, Clock, Cpu, Server, Network, ShieldCheck, ShieldAlert, RefreshCw } from "lucide-react"
import { EnterpriseCard, EnterpriseCardHeader, EnterpriseCardTitle, EnterpriseCardContent } from "@/components/ui/EnterpriseCard"
import { API_BASE_URL } from "@/lib/api"
import { motion } from "framer-motion"

interface HealthData {
  status: string
  version?: string
  uptime?: string
}

interface TimelineStep {
  name: string
  ms: number
  color: string
  pct: number
}

// Removed mock metrics and timelines. Real implementations should fetch from backend.

function MetricCard({ icon: Icon, label, value, delay = 0 }: { icon: any, label: string, value: string, delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
    >
      <EnterpriseCard>
        <EnterpriseCardContent className="p-5 flex flex-col justify-center min-h-[110px]">
          <div className="flex items-center gap-2 text-ash text-caption-sm font-medium uppercase tracking-wider mb-3">
            <Icon className="h-4 w-4" /> {label}
          </div>
          <div className="text-display-sm text-ink font-mono tabular-nums">{value}</div>
        </EnterpriseCardContent>
      </EnterpriseCard>
    </motion.div>
  )
}

export default function MonitoringPage() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchHealth = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await fetch(`${API_BASE_URL}/api/health`)
      if (!res.ok) throw new Error(`Status ${res.status}`)
      const data = await res.json()
      setHealth(data)
    } catch (err: any) {
      setError(err.message || "Failed to reach backend")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchHealth() }, [])

  const isHealthy = health?.status === "ok" || health?.status === "healthy"

  return (
    <div className="flex flex-col min-h-screen p-6 md:p-8 lg:p-10">
      <div className="w-full max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-10 gap-4">
          <div>
            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-display-lg text-ink tracking-tight flex items-center gap-3"
            >
              <Activity className="h-8 w-8 text-accent-blue" />
              Execution Monitoring
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="text-body-lg text-mute mt-2"
            >
              Real-time execution timelines, performance metrics, and resource monitoring.
            </motion.p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchHealth}
              className="p-2 border border-hairline rounded-[var(--radius-md)] bg-surface text-mute hover:bg-surface-elevated hover:text-body transition-colors"
              aria-label="Refresh health status"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            {loading ? (
              <div className="flex items-center gap-2 px-4 py-2 bg-surface border border-hairline rounded-[var(--radius-md)] text-caption-md text-mute">
                <span className="h-2 w-2 rounded-full bg-mute animate-pulse" /> Checking...
              </div>
            ) : error ? (
              <div className="flex items-center gap-2 px-4 py-2 bg-accent-red-soft border border-accent-red-soft rounded-[var(--radius-md)] text-caption-md text-accent-red font-medium">
                <ShieldAlert className="w-4 h-4" /> Unreachable
              </div>
            ) : (
              <div className={`flex items-center gap-2 px-4 py-2 border rounded-[var(--radius-md)] text-caption-md font-medium ${isHealthy ? 'bg-accent-green-soft border-accent-green-soft text-accent-green' : 'bg-accent-yellow-soft border-accent-yellow-soft text-accent-yellow'}`}>
                <ShieldCheck className="w-4 h-4" /> {isHealthy ? 'System Healthy' : 'Degraded'}
              </div>
            )}
          </div>
        </div>

        {/* KPI Row */}
        <div className="grid grid-cols-1 mb-8">
          <EnterpriseCard>
            <div className="flex flex-col items-center justify-center p-12 text-center gap-2">
              <Activity className="h-8 w-8 text-ash" />
              <p className="text-body-sm text-mute">No execution metrics available from backend yet.</p>
            </div>
          </EnterpriseCard>
        </div>

        {/* Execution Timeline */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <EnterpriseCard className="mb-8">
            <EnterpriseCardHeader>
              <EnterpriseCardTitle>Execution Timeline</EnterpriseCardTitle>
            </EnterpriseCardHeader>
            <EnterpriseCardContent>
              <div className="flex flex-col items-center justify-center p-12 text-center gap-2">
                <Clock className="h-8 w-8 text-ash" />
                <p className="text-body-sm text-mute">No timeline data available.</p>
              </div>
            </EnterpriseCardContent>
          </EnterpriseCard>
        </motion.div>
      </div>
    </div>
  )
}
