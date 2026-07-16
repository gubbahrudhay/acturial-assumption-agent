"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { motion, AnimatePresence } from "framer-motion"
import { Badge } from "@/components/ui/badge"
import { GitMerge, Activity, BrainCircuit, BarChart, FileText, Search, Play, Pause, SkipBack, SkipForward, Menu, X, ArrowRight, TrendingUp } from "lucide-react"
import Link from "next/link"
import { useStore } from "@/store/store"
import { API_BASE_URL } from "@/lib/api"

import RootCauseBanner from "@/components/investigation/RootCauseBanner"
import InvestigationProgress from "@/components/investigation/InvestigationProgress"
import CommandPalette from "@/components/investigation/CommandPalette"
import PlannerNotebookTimeline from "@/components/investigation/PlannerNotebookTimeline"
import RootCausePanel from "@/components/RootCausePanel"
import ComparisonWorkspace from "@/components/ComparisonWorkspace"

// Charts (Simplified)
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, BarChart as RechartsBarChart, Bar, Cell } from 'recharts'

export default function InvestigationWorkspace() {
  const { 
    dataset, drift, investigationTree, businessImpact, 
    plannerNotebook, eventReconstruction, decisionOptions, copilotMessages,
    primaryRootCause, explainabilityReport,
    isLoading, setLoading, setAgentData, addCopilotMessage, setBusinessImpact
  } = useStore()
  
  const [chatInput, setChatInput] = useState("")
  const [isCopilotOpen, setIsCopilotOpen] = useState(false)
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false)
  const [activeExplainability, setActiveExplainability] = useState<any>(null)
  const [activeView, setActiveView] = useState("investigation")
  const [activeTab, setActiveTab] = useState("frequency")
  
  const [isReplaying, setIsReplaying] = useState(false)
  const [replayStep, setReplayStep] = useState(0)

  useEffect(() => {
    if (drift) {
      if (drift.deterioration_pattern !== undefined) setActiveTab("combined")
      else if (drift.observed_severity !== undefined) setActiveTab("severity")
      else setActiveTab("frequency")
    }
  }, [drift])

  const runFullInvestigation = async () => {
    setLoading(true)
    try {
      const apiKey = localStorage.getItem("gemini_api_key") || ""
      const detectRes = await axios.post(`${API_BASE_URL}/api/contracts/detect`, { dataset: dataset })
      const analyzeRes = await axios.post(`${API_BASE_URL}/api/data-readiness/analyze`, {
        dataset: dataset,
        engine_context: detectRes.data.engine_context
      })
      if (!analyzeRes.data.dataset_ready) {
        window.location.href = '/data-readiness'
        return
      }
      const res = await axios.post(`${API_BASE_URL}/api/agent/run`, { api_key: apiKey, dataset: dataset })
      setAgentData(res.data)
      setReplayStep(res.data.planner_notebook?.length || 0)
    } catch (error) {
      console.error("Error running agent:", error)
    } finally {
      setLoading(false)
    }
  }

  const downloadPdfReport = async () => {
    try {
      setLoading(true)
      const res = await axios.post(`${API_BASE_URL}/api/report/pdf`, { state: useStore.getState() }, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `Investigation_Report_${Date.now()}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error("Error downloading PDF:", error)
    } finally {
      setLoading(false)
    }
  }

  const status = isLoading ? "frequency" : (investigationTree ? "end" : "start")

  return (
    <div className="flex-1 flex flex-col font-sans h-full">
      <CommandPalette 
        isOpen={isCommandPaletteOpen} 
        setIsOpen={setIsCommandPaletteOpen}
        runInvestigation={runFullInvestigation}
        downloadPdf={downloadPdfReport}
        openCopilot={() => setIsCopilotOpen(true)}
      />
      
      {/* Investigation Action Bar */}
      <header className="h-14 bg-surface border-b border-hairline px-6 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-4">
          <Menu className="h-5 w-5 text-ink md:hidden" />
          <h1 className="text-body-strong text-ink flex items-center gap-2">
            <Activity className="text-accent-blue h-4 w-4" />
            Agentic Pricing Copilot
          </h1>
          <Badge variant="outline" className="ml-4 font-mono text-[10px] bg-surface-elevated border-hairline text-mute uppercase">INV-8F92A1B</Badge>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={runFullInvestigation} disabled={isLoading} className="bg-primary hover:bg-primary-pressed text-on-primary px-4 py-1.5 rounded-[var(--radius-sm)] font-medium text-body-sm transition-colors disabled:opacity-50 shadow-sm flex items-center gap-2">
            {isLoading ? <BrainCircuit className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {isLoading ? "Analyzing..." : "Run Analysis"}
          </button>
        </div>
      </header>

      <InvestigationProgress status={status} />

      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Secondary Sidebar */}
        <aside className="w-64 bg-surface border-r border-hairline hidden md:flex flex-col py-6">
          <div className="px-6 mb-8">
            <p className="text-caption-sm font-semibold text-ash uppercase tracking-wider mb-4">Workspace</p>
            <nav className="space-y-1">
              <button onClick={() => setActiveView("investigation")} className={`w-full flex items-center gap-3 px-3 py-2 text-body-sm font-medium rounded-[var(--radius-md)] ${activeView === 'investigation' ? 'bg-accent-blue-soft text-accent-blue' : 'text-body hover:bg-surface-elevated'}`}><Activity className="h-4 w-4" /> Investigation</button>
              <button onClick={() => setActiveView("scenario")} className={`w-full flex items-center gap-3 px-3 py-2 text-body-sm font-medium rounded-[var(--radius-md)] ${activeView === 'scenario' ? 'bg-accent-blue-soft text-accent-blue' : 'text-body hover:bg-surface-elevated'}`}><BarChart className="h-4 w-4" /> Scenario Lab</button>
              <button onClick={() => setActiveView("reports")} className={`w-full flex items-center gap-3 px-3 py-2 text-body-sm font-medium rounded-[var(--radius-md)] ${activeView === 'reports' ? 'bg-accent-blue-soft text-accent-blue' : 'text-body hover:bg-surface-elevated'}`}><FileText className="h-4 w-4" /> Reports</button>
            </nav>
          </div>
        </aside>

        {/* Center Workspace */}
        <main className="flex-1 overflow-y-auto p-8 pb-32">
          <div className="max-w-5xl mx-auto space-y-12">
            
            {activeView === "investigation" && (
              <>
                {investigationTree && businessImpact && (
                  <RootCauseBanner impact={businessImpact} rootCause={primaryRootCause} confidence={drift?.drift_score ? Math.round(drift.drift_score) + "%" : "95%"} />
                )}
                
                {isLoading && (
                  <div className="mt-20 text-center">
                    <BrainCircuit className="h-16 w-16 text-accent-blue animate-pulse mx-auto mb-6" />
                    <h2 className="text-heading-xl text-ink">AI Analyst is working...</h2>
                    <p className="text-body-md text-mute mt-2">Evaluating portfolio segments and simulating business impact.</p>
                  </div>
                )}
                
                {!isLoading && investigationTree && (
                  <div className="space-y-16 mt-8">
                    <PlannerNotebookTimeline 
                      plannerNotebook={plannerNotebook}
                      isReplaying={isReplaying}
                      setIsReplaying={setIsReplaying}
                      replayStep={replayStep}
                      setReplayStep={setReplayStep}
                      setActiveExplainability={setActiveExplainability}
                    />

                    {replayStep >= plannerNotebook.length && decisionOptions.length > 0 && (
                      <section>
                        <h2 className="text-heading-lg text-ink mb-6">Decision Intelligence</h2>
                        <div className="space-y-4">
                          {decisionOptions.map((opt: any, i: number) => (
                            <div key={i} className="bg-surface border border-hairline rounded-[var(--radius-lg)] transition-all overflow-hidden cursor-pointer hover:bg-surface-elevated">
                              <div className="flex flex-col md:flex-row">
                                <div className="md:w-1/3 bg-surface-elevated p-6 border-b border-hairline md:border-b-0 md:border-r">
                                  <Badge className={`mb-3 shadow-none uppercase tracking-wider text-[10px] ${opt.suggested_priority === 'High' ? 'bg-accent-red-soft text-accent-red border-accent-red-soft' : 'bg-accent-green-soft text-accent-green border-accent-green-soft'}`}>{opt.suggested_priority} Priority</Badge>
                                  <h3 className="text-heading-sm text-ink">{opt.possible_action}</h3>
                                </div>
                                <div className="md:w-2/3 p-6 grid grid-cols-2 gap-6">
                                  <div>
                                    <p className="text-caption-sm font-bold text-accent-green uppercase tracking-wider mb-2">Benefits</p>
                                    <p className="text-body-sm text-body">{opt.benefits}</p>
                                  </div>
                                  <div>
                                    <p className="text-caption-sm font-bold text-accent-red uppercase tracking-wider mb-2">Risks</p>
                                    <p className="text-body-sm text-body">{opt.risks}</p>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </section>
                    )}
                  </div>
                )}
              </>
            )}

            {/* Bottom padding for docked copilot */}
            <div className="h-32" />
          </div>
        </main>
      </div>
    </div>
  )
}
