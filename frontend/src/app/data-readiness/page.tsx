"use client"

import { useState, useEffect } from "react"
import { ShieldCheck, AlertCircle, Database, CheckCircle2, XCircle, Activity, BarChart3, AlertTriangle, Play } from "lucide-react"
import { useStore } from "@/store/store"

export default function DataReadinessPage() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const { dataset } = useStore()

  const runReadinessCheck = async () => {
    if (!dataset) return;
    setLoading(true)
    try {
      const detectRes = await fetch("http://localhost:8000/api/contracts/detect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset })
      })
      const detectData = await detectRes.json()

      const analyzeRes = await fetch("http://localhost:8000/api/data-readiness/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          dataset,
          engine_context: detectData.engine_context
        })
      })
      const analyzeData = await analyzeRes.json()

      setData({ detect: detectData, analyze: analyzeData })
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  // Run automatically on first mount if we have a dataset, but don't re-run automatically on change
  useEffect(() => {
    if (dataset && !data && !loading) {
      runReadinessCheck()
    }
  }, [dataset])

  if (loading && !data) {
    return (
      <div className="flex h-[calc(100vh-80px)] items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#ff385c]"></div>
      </div>
    )
  }

  const { detect, analyze } = data || {}
  const capabilityMatrix = detect?.compatibility?.capability_matrix || []
  const findings = analyze?.findings || { critical: [], errors: [], warnings: [], info: [] }
  const isReady = analyze?.dataset_ready

  return (
    <div className="py-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[#222222] flex items-center gap-2">
            <ShieldCheck className="h-8 w-8 text-[#ff385c]" />
            Enterprise Data Readiness
          </h1>
          <p className="text-[#6a6a6a] mt-2">
            Dataset validation, contract detection, and engine compatibility matrix.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={runReadinessCheck}
            disabled={loading || !dataset}
            className="flex items-center gap-2 bg-[#ff385c] hover:bg-[#d90b2e] text-white px-6 py-3 rounded-full font-bold transition-colors disabled:opacity-50"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : (
              <Play className="h-5 w-5" />
            )}
            {loading ? "Analyzing..." : "Run Readiness Check"}
          </button>
          
          {data && (
            <div className={`px-6 py-3 rounded-full font-bold flex items-center gap-2 ${isReady ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              {isReady ? <CheckCircle2 className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
              {isReady ? "Dataset Ready for Investigation" : "Critical Validation Errors"}
            </div>
          )}
        </div>
      </div>

      {data ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2 bg-white rounded-xl border border-[#dddddd] shadow-sm p-6">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Database className="h-5 w-5 text-[#6a6a6a]" />
              Dataset Overview & Contract
            </h2>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-500 mb-1">Detected Contract</div>
                <div className="font-bold text-lg">{detect?.contract_type || "Unknown"}</div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-500 mb-1">Schema Version</div>
                <div className="font-bold text-lg">{detect?.engine_context?.schema_version || "1"}</div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-500 mb-1">Recommended Engine</div>
                <div className="font-bold text-lg text-blue-600">{detect?.compatibility?.recommended_engine || "None"}</div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-500 mb-1">Overall Quality Score</div>
                <div className="font-bold text-lg text-green-600">{analyze?.overall_score || 0} / 100</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-[#dddddd] shadow-sm p-6">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Activity className="h-5 w-5 text-[#6a6a6a]" />
              Capability Matrix
            </h2>
            <div className="space-y-3">
              {capabilityMatrix.map((cap: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-gray-100 bg-gray-50">
                  <div className="font-medium">{cap.Investigation}</div>
                  <div className="flex items-center gap-2 text-sm">
                    {cap.Status === "Ready" ? (
                      <span className="text-green-600 font-medium flex items-center gap-1"><CheckCircle2 className="h-4 w-4"/> Ready</span>
                    ) : (
                      <span className="text-gray-500 flex items-center gap-1"><XCircle className="h-4 w-4"/> {cap.Reason}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center p-16 bg-white border border-[#dddddd] rounded-xl shadow-sm mb-8 text-center">
          <Database className="h-16 w-16 text-[#dddddd] mb-4" />
          <h2 className="text-xl font-bold text-[#222222] mb-2">No Readiness Data</h2>
          <p className="text-[#6a6a6a] max-w-md">
            Click the "Run Readiness Check" button above to analyze the currently selected dataset and view its contract and compatibility matrix.
          </p>
        </div>
      )}

      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-red-200 shadow-sm p-6">
            <h2 className="text-lg font-bold text-red-700 mb-4 flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Critical Errors
            </h2>
            {findings.critical.length > 0 ? (
              <ul className="space-y-2">
                {findings.critical.map((err: string, i: number) => (
                  <li key={i} className="text-red-600 bg-red-50 p-3 rounded-lg border border-red-100">{err}</li>
                ))}
              </ul>
            ) : (
              <div className="text-gray-500 bg-gray-50 p-4 rounded-lg flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-500" />
                No critical schema errors detected.
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl border border-amber-200 shadow-sm p-6">
            <h2 className="text-lg font-bold text-amber-700 mb-4 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Warnings & Missing Data
            </h2>
            {findings.warnings.length > 0 || findings.errors.length > 0 ? (
              <ul className="space-y-2">
                {findings.errors.map((err: string, i: number) => (
                  <li key={`err-${i}`} className="text-orange-600 bg-orange-50 p-3 rounded-lg border border-orange-100">{err}</li>
                ))}
                {findings.warnings.map((warn: string, i: number) => (
                  <li key={`warn-${i}`} className="text-amber-600 bg-amber-50 p-3 rounded-lg border border-amber-100">{warn}</li>
                ))}
              </ul>
            ) : (
              <div className="text-gray-500 bg-gray-50 p-4 rounded-lg flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-500" />
                No missing data or warnings detected.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
