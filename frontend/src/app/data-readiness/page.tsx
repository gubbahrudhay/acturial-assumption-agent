"use client"

import { useState, useEffect } from "react"
import { ShieldCheck, AlertCircle, Database, CheckCircle2, XCircle, Activity, AlertTriangle, Play, RefreshCw } from "lucide-react"
import { useStore } from "@/store/store"
import { API_BASE_URL } from "@/lib/api"
import { EnterpriseCard, EnterpriseCardHeader, EnterpriseCardTitle, EnterpriseCardContent } from "@/components/ui/EnterpriseCard"
import { motion } from "framer-motion"

export default function DataReadinessPage() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { dataset } = useStore()

  const runReadinessCheck = async () => {
    if (!dataset) return;
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const detectRes = await fetch(`${API_BASE_URL}/api/contracts/detect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset })
      })
      if (!detectRes.ok) throw new Error(`Contract detection failed (${detectRes.status})`)
      const detectData = await detectRes.json()

      const analyzeRes = await fetch(`${API_BASE_URL}/api/data-readiness/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          dataset,
          engine_context: detectData.engine_context
        })
      })
      if (!analyzeRes.ok) throw new Error(`Readiness analysis failed (${analyzeRes.status})`)
      const analyzeData = await analyzeRes.json()

      setData({ detect: detectData, analyze: analyzeData })
    } catch (e: any) {
      setError(e.message || "Failed to run readiness check")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (dataset) {
      runReadinessCheck()
    }
  }, [dataset])

  const { detect, analyze } = data || {}
  const capabilityMatrix = detect?.compatibility?.capability_matrix || []
  const findings = analyze?.findings || { critical: [], errors: [], warnings: [], info: [] }
  const isReady = analyze?.dataset_ready

  return (
    <div className="flex flex-col min-h-screen p-6 md:p-8 lg:p-10">
      <div className="w-full max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-10 gap-4">
          <div>
            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-display-lg text-ink flex items-center gap-3"
            >
              <ShieldCheck className="h-8 w-8 text-accent-blue" />
              Data Readiness
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="text-body-lg text-mute mt-2"
            >
              Dataset validation, contract detection, and engine compatibility matrix.
            </motion.p>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <button 
              onClick={runReadinessCheck}
              disabled={loading || !dataset}
              className="flex items-center gap-2 bg-primary hover:bg-primary-pressed text-on-primary px-5 py-2.5 rounded-[var(--radius-md)] text-body-sm-strong transition-colors disabled:opacity-50"
              aria-label="Run readiness check"
            >
              {loading ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              {loading ? "Analyzing..." : "Run Readiness Check"}
            </button>
            
            {data && (
              <div className={`px-3 py-2 rounded-[var(--radius-md)] font-medium text-caption-md flex items-center gap-2 border ${isReady ? 'bg-accent-green-soft text-accent-green border-accent-green-soft' : 'bg-accent-red-soft text-accent-red border-accent-red-soft'}`}>
                {isReady ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                {isReady ? "Dataset Ready" : "Validation Errors"}
              </div>
            )}
          </div>
        </div>

        {/* Loading State */}
        {loading && !data && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div className="lg:col-span-2 skeleton h-[220px] rounded-[var(--radius-xl)]" />
            <div className="skeleton h-[220px] rounded-[var(--radius-xl)]" />
          </div>
        )}

        {/* Error State */}
        {error && !data && (
          <EnterpriseCard className="mb-8">
            <div className="flex flex-col items-center justify-center p-12 text-center gap-3">
              <AlertCircle className="h-8 w-8 text-accent-red" />
              <p className="text-body-sm text-mute">{error}</p>
              <button onClick={runReadinessCheck} className="text-accent-blue text-body-sm-strong hover:underline">
                Retry
              </button>
            </div>
          </EnterpriseCard>
        )}

        {/* Results */}
        {data ? (
          <>
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6"
            >
              <EnterpriseCard className="lg:col-span-2">
                <EnterpriseCardHeader>
                  <EnterpriseCardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5 text-accent-blue" />
                    Dataset Overview & Contract
                  </EnterpriseCardTitle>
                </EnterpriseCardHeader>
                <EnterpriseCardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-surface-elevated rounded-[var(--radius-lg)] border border-hairline flex flex-col justify-center min-h-[90px]">
                      <div className="text-caption-sm font-medium uppercase tracking-wider text-ash mb-1.5">Detected Contract</div>
                      <div className="text-heading-sm text-ink">{detect?.contract_type || "Unknown"}</div>
                    </div>
                    <div className="p-4 bg-surface-elevated rounded-[var(--radius-lg)] border border-hairline flex flex-col justify-center min-h-[90px]">
                      <div className="text-caption-sm font-medium uppercase tracking-wider text-ash mb-1.5">Schema Version</div>
                      <div className="text-heading-sm text-ink tabular-nums">{detect?.engine_context?.schema_version || "1"}</div>
                    </div>
                    <div className="p-4 bg-surface-elevated rounded-[var(--radius-lg)] border border-hairline flex flex-col justify-center min-h-[90px]">
                      <div className="text-caption-sm font-medium uppercase tracking-wider text-ash mb-1.5">Recommended Engine</div>
                      <div className="text-heading-sm text-accent-blue">{detect?.compatibility?.recommended_engine || "None"}</div>
                    </div>
                    <div className="p-4 bg-surface-elevated rounded-[var(--radius-lg)] border border-hairline flex flex-col justify-center min-h-[90px]">
                      <div className="text-caption-sm font-medium uppercase tracking-wider text-ash mb-1.5">Quality Score</div>
                      <div className="text-heading-sm text-accent-green tabular-nums">{analyze?.overall_score || 0} / 100</div>
                    </div>
                  </div>
                </EnterpriseCardContent>
              </EnterpriseCard>

              <EnterpriseCard>
                <EnterpriseCardHeader>
                  <EnterpriseCardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-accent-blue" />
                    Capability Matrix
                  </EnterpriseCardTitle>
                </EnterpriseCardHeader>
                <EnterpriseCardContent>
                  {capabilityMatrix.length > 0 ? (
                    <div className="space-y-2">
                      {capabilityMatrix.map((cap: any, i: number) => (
                        <div key={i} className="flex items-center justify-between p-3 rounded-[var(--radius-md)] border border-hairline bg-surface-elevated">
                          <span className="font-medium text-body-sm text-ink">{cap.Investigation}</span>
                          {cap.Status === "Ready" ? (
                            <span className="text-accent-green text-caption-sm font-medium flex items-center gap-1"><CheckCircle2 className="h-3.5 w-3.5"/> Ready</span>
                          ) : (
                            <span className="text-mute text-caption-sm flex items-center gap-1"><XCircle className="h-3.5 w-3.5"/> {cap.Reason}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-body-sm text-mute text-center p-4">No capability data available.</div>
                  )}
                </EnterpriseCardContent>
              </EnterpriseCard>
            </motion.div>

            {/* Findings */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="grid grid-cols-1 lg:grid-cols-2 gap-6"
            >
              <EnterpriseCard>
                <EnterpriseCardHeader>
                  <EnterpriseCardTitle className="flex items-center gap-2 text-accent-red">
                    <AlertCircle className="h-5 w-5" />
                    Critical Errors
                  </EnterpriseCardTitle>
                </EnterpriseCardHeader>
                <EnterpriseCardContent>
                  {findings.critical.length > 0 ? (
                    <ul className="space-y-2" role="list">
                      {findings.critical.map((err: string, i: number) => (
                        <li key={i} className="text-accent-red bg-accent-red-soft p-3 rounded-[var(--radius-md)] border border-accent-red-soft text-body-sm font-medium">{err}</li>
                      ))}
                    </ul>
                  ) : (
                    <div className="text-accent-green bg-accent-green-soft p-4 rounded-[var(--radius-md)] flex items-center gap-2 border border-accent-green-soft text-body-sm font-medium">
                      <CheckCircle2 className="h-5 w-5 shrink-0" />
                      No critical schema errors detected.
                    </div>
                  )}
                </EnterpriseCardContent>
              </EnterpriseCard>

              <EnterpriseCard>
                <EnterpriseCardHeader>
                  <EnterpriseCardTitle className="flex items-center gap-2 text-accent-yellow">
                    <AlertTriangle className="h-5 w-5" />
                    Warnings & Missing Data
                  </EnterpriseCardTitle>
                </EnterpriseCardHeader>
                <EnterpriseCardContent>
                  {findings.warnings.length > 0 || findings.errors.length > 0 ? (
                    <ul className="space-y-2" role="list">
                      {findings.errors.map((err: string, i: number) => (
                        <li key={`err-${i}`} className="text-accent-yellow bg-accent-yellow-soft p-3 rounded-[var(--radius-md)] border border-accent-yellow-soft text-body-sm font-medium">{err}</li>
                      ))}
                      {findings.warnings.map((warn: string, i: number) => (
                        <li key={`warn-${i}`} className="text-accent-yellow bg-accent-yellow-soft p-3 rounded-[var(--radius-md)] border border-accent-yellow-soft text-body-sm font-medium">{warn}</li>
                      ))}
                    </ul>
                  ) : (
                    <div className="text-accent-green bg-accent-green-soft p-4 rounded-[var(--radius-md)] flex items-center gap-2 border border-accent-green-soft text-body-sm font-medium">
                      <CheckCircle2 className="h-5 w-5 shrink-0" />
                      No missing data or warnings detected.
                    </div>
                  )}
                </EnterpriseCardContent>
              </EnterpriseCard>
            </motion.div>
          </>
        ) : !loading && !error && (
          <EnterpriseCard className="mb-8">
            <div className="flex flex-col items-center justify-center p-16 text-center">
              <Database className="h-12 w-12 text-ash mb-4" />
              <h2 className="text-heading-lg text-ink mb-2">No Readiness Data</h2>
              <p className="text-body-sm text-mute max-w-md">
                Click the "Run Readiness Check" button above to analyze the currently selected dataset and view its contract and compatibility matrix.
              </p>
            </div>
          </EnterpriseCard>
        )}
      </div>
    </div>
  )
}
