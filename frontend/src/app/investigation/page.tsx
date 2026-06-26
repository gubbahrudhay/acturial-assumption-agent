"use client"

import { useState, useEffect, useRef } from "react"
import axios from "axios"
import { motion, AnimatePresence } from "framer-motion"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { GitMerge, Activity, BrainCircuit, BarChart, BarChart3, FileText, MessageSquare, ShieldAlert, Search, Play, Pause, SkipBack, SkipForward, Menu, X, ArrowRight } from "lucide-react"
import Link from "next/link"
import { useStore } from "@/store/store"
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, BarChart as RechartsBarChart, Bar, Cell
} from 'recharts';
import RootCausePanel from "@/components/RootCausePanel";
import ReplayControls from "@/components/ReplayControls";
import ComparisonWorkspace from "@/components/ComparisonWorkspace";

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
  
  // Replay state
  const [isReplaying, setIsReplaying] = useState(false)
  const [replayStep, setReplayStep] = useState(0)
  
  // Investigation Pipeline Progress
  const pipelineSteps = [
    { id: 'data', label: 'Dataset Loaded' },
    { id: 'drift', label: 'Drift Detected' },
    { id: 'portfolio', label: 'Evidence Collected' },
    { id: 'impact', label: 'Business Impact' },
    { id: 'decisions', label: 'Decision Support' },
    { id: 'report', label: 'Report Generated' }
  ];
  
  const currentPipelineStep = isLoading ? 2 : (investigationTree ? 5 : 0);

  // Command Palette Keyboard Shortcut
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setIsCommandPaletteOpen((open) => !open)
      }
    }
    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [])

  const runFullInvestigation = async () => {
    setLoading(true)
    try {
      const apiKey = localStorage.getItem("gemini_api_key") || ""
      const res = await axios.post("http://localhost:8000/api/agent/run", { 
        api_key: apiKey,
        dataset: dataset 
      })
      setAgentData(res.data)
      setReplayStep(res.data.planner_notebook?.length || 0)
    } catch (error) {
      console.error("Error running agent:", error)
    } finally {
      setLoading(false)
    }
  }

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return
    const msg = chatInput
    setChatInput("")
    addCopilotMessage({ role: "user", content: msg })
    
    try {
      const apiKey = localStorage.getItem("gemini_api_key") || ""
      const res = await axios.post("http://localhost:8000/api/chat", {
        state: { 
          api_key: apiKey,
          business_impact: businessImpact,
          decision_options: decisionOptions,
          investigation_memory: investigationTree ? [investigationTree] : [],
          chat_history: copilotMessages
        },
        message: msg
      })
      if (res.data.reply) {
        addCopilotMessage({ role: "assistant", content: res.data.reply })
      }
    } catch (error) {
      console.error("Error sending chat:", error)
    }
  }

  // --- Visualizations ---
  const DriftTrendChart = () => {
    // Mock data for drift trend if not provided by backend yet
    const data = [
      { month: 'Jan', drift: 2.1 },
      { month: 'Feb', drift: 3.4 },
      { month: 'Mar', drift: 5.2 },
      { month: 'Apr', drift: 8.7 },
      { month: 'May', drift: 12.4 },
      { month: 'Jun', drift: (businessImpact?.drift_percentage * 100) || 14.2 },
    ];
    return (
      <div className="h-64 w-full mt-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#ebebeb" />
            <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{fill: '#6a6a6a', fontSize: 12}} />
            <YAxis axisLine={false} tickLine={false} tick={{fill: '#6a6a6a', fontSize: 12}} tickFormatter={(v) => `+${v}%`} />
            <RechartsTooltip contentStyle={{borderRadius: '8px', border: '1px solid #ebebeb', boxShadow: '0 4px 12px rgba(0,0,0,0.05)'}} />
            <Line type="monotone" dataKey="drift" stroke="#ff385c" strokeWidth={3} dot={{r: 4, fill: '#ff385c', strokeWidth: 0}} activeDot={{r: 6}} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    )
  }

  const TreeNode = ({ node, depth = 0 }: { node: any, depth?: number }) => {
    if (!node) return null;
    const isProblematic = Math.abs(node.actual_frequency - node.expected_frequency) > 0.05; // simplified check
    
    return (
      <div className={`ml-${depth > 0 ? '8' : '0'} mt-4`}>
        <motion.div 
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
          className={`bg-white rounded-xl border ${isProblematic ? 'border-[#ff385c] shadow-sm' : 'border-[#ebebeb]'} overflow-hidden cursor-pointer hover:shadow-md transition-shadow`}
          onClick={() => setActiveExplainability({type: 'node', data: node})}
        >
          <div className={`py-3 px-5 border-b flex justify-between items-center ${isProblematic ? 'bg-[#fff0f2] border-[#ff385c]/20' : 'bg-[#f7f7f7] border-[#ebebeb]'}`}>
            <div className="flex items-center gap-2">
              <GitMerge className={`h-4 w-4 ${isProblematic ? 'text-[#ff385c]' : 'text-[#6a6a6a]'}`} />
              <span className="font-bold text-[#222222] text-sm">{node.name === 'Root' ? 'Total Portfolio' : (node.name || '').replace('Root -> ', '') || 'Unknown Node'}</span>
            </div>
            {isProblematic && <Badge className="bg-[#ff385c] hover:bg-[#ff385c] text-white shadow-none uppercase text-[10px] tracking-wider">High Drift</Badge>}
          </div>
          <div className="p-5 flex gap-8">
            <div>
              <p className="text-[10px] uppercase font-bold text-[#aaaaaa] mb-1">Exposure</p>
              <p className="text-[#222222] font-semibold text-sm">{node.exposure?.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-[#aaaaaa] mb-1">Expected</p>
              <p className="text-[#6a6a6a] font-semibold text-sm">{(node.expected_frequency * 100).toFixed(2)}%</p>
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-[#aaaaaa] mb-1">Actual</p>
              <p className={`font-bold text-sm ${isProblematic ? 'text-[#ff385c]' : 'text-[#222222]'}`}>{(node.actual_frequency * 100).toFixed(2)}%</p>
            </div>
          </div>
        </motion.div>
        
        {node.children && node.children.map((child: any, idx: number) => (
          <div key={idx} className="relative">
            <div className="absolute top-0 left-6 w-px h-full bg-[#ebebeb] -z-10" />
            <div className="absolute top-8 left-6 w-4 h-px bg-[#ebebeb] -z-10" />
            <TreeNode node={child} depth={depth + 1} />
          </div>
        ))}
      </div>
    )
  }

  // --- Components ---

  const downloadPdfReport = async () => {
    try {
      setLoading(true)
      const res = await axios.post("http://localhost:8000/api/report/pdf", {
        state: useStore.getState()
      }, { responseType: 'blob' })
      
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

  const CommandPalette = () => (
    <AnimatePresence>
      {isCommandPaletteOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/40 backdrop-blur-sm" onClick={() => setIsCommandPaletteOpen(false)}>
          <motion.div 
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            onClick={e => e.stopPropagation()}
            className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden border border-[#ebebeb]"
          >
            <div className="flex items-center px-4 py-3 border-b border-[#ebebeb]">
              <Search className="h-5 w-5 text-[#6a6a6a] mr-3" />
              <input 
                autoFocus
                placeholder="Search investigations, reports, actions..." 
                className="flex-1 bg-transparent text-[#222222] placeholder-[#6a6a6a] outline-none text-[16px]"
              />
              <Badge className="bg-[#f0f0f0] text-[#6a6a6a] font-mono shadow-none hover:bg-[#f0f0f0]">ESC</Badge>
            </div>
            <div className="p-2">
              <div className="px-3 py-2 text-xs font-semibold text-[#6a6a6a] uppercase tracking-wider">Actions</div>
              <button onClick={() => {runFullInvestigation(); setIsCommandPaletteOpen(false)}} className="w-full text-left px-3 py-3 rounded-lg hover:bg-[#f7f7f7] flex items-center group">
                <Play className="h-4 w-4 mr-3 text-[#ff385c]" />
                <span className="text-[#222222] font-medium">Run Full Investigation</span>
              </button>
              <Link href="/analytics" onClick={() => setIsCommandPaletteOpen(false)} className="w-full text-left px-3 py-3 rounded-lg hover:bg-[#f7f7f7] flex items-center group">
                <BarChart3 className="h-4 w-4 mr-3 text-[#137333]" />
                <span className="text-[#222222] font-medium">View Analytics Dashboard</span>
              </Link>
              <button onClick={() => {setIsCopilotOpen(true); setIsCommandPaletteOpen(false)}} className="w-full text-left px-3 py-3 rounded-lg hover:bg-[#f7f7f7] flex items-center group">
                <MessageSquare className="h-4 w-4 mr-3 text-[#fbbc04]" />
                <span className="text-[#222222] font-medium">Open AI Copilot</span>
              </button>
              <button onClick={() => {downloadPdfReport(); setIsCommandPaletteOpen(false)}} className="w-full text-left px-3 py-3 rounded-lg hover:bg-[#f7f7f7] flex items-center group">
                <FileText className="h-4 w-4 mr-3 text-[#222222]" />
                <span className="text-[#222222] font-medium">Export Report to PDF</span>
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )

  const ProgressTimeline = () => (
    <div className="w-full overflow-x-auto pb-4 mb-8">
      <div className="flex items-center min-w-max">
        {pipelineSteps.map((step, idx) => (
          <div key={step.id} className="flex items-center">
            <div className={`flex flex-col items-center justify-center ${idx <= currentPipelineStep ? 'opacity-100' : 'opacity-40'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shadow-sm transition-colors duration-500
                ${idx < currentPipelineStep ? 'bg-[#137333] text-white' : 
                  idx === currentPipelineStep && isLoading ? 'bg-[#fbbc04] text-black animate-pulse' : 
                  idx === currentPipelineStep ? 'bg-[#ff385c] text-white' : 
                  'bg-[#f0f0f0] text-[#6a6a6a]'}`}
              >
                {idx < currentPipelineStep ? '✓' : (idx + 1)}
              </div>
              <span className={`text-[11px] font-bold mt-2 uppercase tracking-wider ${idx <= currentPipelineStep ? 'text-[#222222]' : 'text-[#6a6a6a]'}`}>{step.label}</span>
            </div>
            {idx < pipelineSteps.length - 1 && (
              <div className="w-16 h-px mx-2 relative">
                <div className="absolute top-0 left-0 h-full bg-[#ebebeb] w-full" />
                <motion.div 
                  className="absolute top-0 left-0 h-full bg-[#137333]"
                  initial={{ width: '0%' }}
                  animate={{ width: idx < currentPipelineStep ? '100%' : '0%' }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )

  const ConfidenceBanner = () => {
    if (!businessImpact || !investigationTree) return null;
    return (
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 p-6 bg-gradient-to-r from-[#222222] to-[#111111] rounded-2xl shadow-xl border border-[#333333]"
      >
        <div className="flex flex-col md:flex-row justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <BrainCircuit className="text-[#ff385c] h-5 w-5" />
              <h2 className="text-white font-bold text-lg">Investigation Complete</h2>
            </div>
            <p className="text-[#aaaaaa] text-sm max-w-xl">
              The AI has concluded its root cause analysis and impact assessment. Review the generated decisions below.
            </p>
          </div>
          <div className="flex flex-wrap gap-4 md:gap-6 mt-6">
            <div className="bg-[#333333]/50 px-4 py-3 rounded-xl border border-[#444444]">
              <p className="text-[#aaaaaa] text-[11px] uppercase tracking-wider font-bold mb-1">Root Cause Segment</p>
              <p className="text-white font-bold truncate max-w-[200px]">{investigationTree?.name ? investigationTree.name.replace('Root -> ', '') : 'Unknown'}</p>
            </div>
            <div className="bg-[#333333]/50 px-4 py-3 rounded-xl border border-[#444444]">
              <p className="text-[#aaaaaa] text-[11px] uppercase tracking-wider font-bold mb-1">Business Impact</p>
              <p className={`font-bold ${businessImpact?.risk_level === 'High' ? 'text-[#ff385c]' : 'text-[#fbbc04]'}`}>
                {businessImpact?.risk_level || 'Unknown'} Risk
              </p>
            </div>
            <div className="bg-[#333333]/50 px-4 py-3 rounded-xl border border-[#444444]">
              <p className="text-[#aaaaaa] text-[11px] uppercase tracking-wider font-bold mb-1">Statistical Confidence</p>
              <p className={`font-bold ${drift?.drift_score > 70 ? 'text-[#137333]' : 'text-[#fbbc04]'}`}>
                {drift?.drift_score ? Math.round(drift.drift_score) : 0}%
              </p>
            </div>
            <div className="bg-[#333333]/50 px-4 py-3 rounded-xl border border-[#444444] relative group">
              <p className="text-[#aaaaaa] text-[11px] uppercase tracking-wider font-bold mb-1 flex items-center gap-1">
                Explainability Score
              </p>
              <p className={`font-bold ${explainabilityReport?.overall_score > 70 ? 'text-[#137333]' : 'text-[#fbbc04]'}`}>
                {explainabilityReport?.overall_score || 0}%
              </p>
            </div>
          </div>
        </div>
      </motion.div>
    )
  }

  const PlannerNotebookTimeline = () => {
    if (!plannerNotebook || plannerNotebook.length === 0) return null;
    const displaySteps = isReplaying ? plannerNotebook.slice(0, replayStep) : plannerNotebook;
    
    return (
      <div className="mb-12">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-[#222222]">AI Execution Timeline</h2>
          <div className="flex items-center gap-2">
            <button onClick={() => {setIsReplaying(true); setReplayStep(Math.max(1, replayStep - 1))}} className="p-2 hover:bg-[#f0f0f0] rounded-full transition-colors"><SkipBack className="h-4 w-4" /></button>
            {isReplaying ? (
               <button onClick={() => setIsReplaying(false)} className="p-2 hover:bg-[#f0f0f0] rounded-full transition-colors"><Pause className="h-4 w-4" /></button>
            ) : (
               <button onClick={() => {setIsReplaying(true); if(replayStep === plannerNotebook.length) setReplayStep(1); }} className="p-2 hover:bg-[#f0f0f0] rounded-full transition-colors"><Play className="h-4 w-4" /></button>
            )}
            <button onClick={() => {setIsReplaying(true); setReplayStep(Math.min(plannerNotebook.length, replayStep + 1))}} className="p-2 hover:bg-[#f0f0f0] rounded-full transition-colors"><SkipForward className="h-4 w-4" /></button>
          </div>
        </div>
        
        <div className="space-y-6">
          <AnimatePresence>
            {displaySteps.map((entry: any, i: number) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
                className="flex"
              >
                <div className="flex flex-col items-center mr-6">
                  <div className="w-8 h-8 rounded-full bg-[#f7f7f7] border border-[#dddddd] flex items-center justify-center text-xs font-bold text-[#6a6a6a] z-10">
                    {i+1}
                  </div>
                  {i < displaySteps.length - 1 && <div className="w-px h-full bg-[#ebebeb] mt-2" />}
                </div>
                <div className="flex-1 bg-white border border-[#dddddd] rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                     onClick={() => setActiveExplainability({type: 'step', data: entry})}>
                  <div className="grid grid-cols-1 gap-3 text-sm">
                    <div className="flex"><span className="w-24 shrink-0 font-bold text-[#6a6a6a]">Observation</span> <span className="text-[#222222]">{entry.observation}</span></div>
                    <div className="flex"><span className="w-24 shrink-0 font-bold text-[#6a6a6a]">Hypothesis</span> <span className="text-[#222222]">{entry.hypothesis}</span></div>
                    <div className="flex"><span className="w-24 shrink-0 font-bold text-[#137333]">Decision</span> <span className="text-[#222222] font-medium">{entry.decision}</span></div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    )
  }

  // --- Main Render ---
  
  return (
    <div className="min-h-screen bg-[#fafafa] flex flex-col font-sans">
      <CommandPalette />
      
      {/* Top Navbar */}
      <header className="h-16 bg-white border-b border-[#ebebeb] px-6 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-4">
          <Menu className="h-5 w-5 text-[#222222] md:hidden" />
          <h1 className="text-xl font-bold text-[#222222] flex items-center gap-2">
            <Activity className="text-[#ff385c]" />
            Antigravity Copilot
          </h1>
          <Badge variant="outline" className="ml-4 font-mono text-[10px] bg-[#f7f7f7]">INV-8F92A1B</Badge>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setIsCommandPaletteOpen(true)}
            className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-[#f0f0f0] text-[#6a6a6a] rounded-lg text-sm hover:bg-[#e0e0e0] transition-colors"
          >
            <Search className="h-4 w-4" />
            <span>Search...</span>
            <span className="font-mono text-xs border border-[#dddddd] px-1 rounded ml-2">⌘K</span>
          </button>
          <button 
            onClick={runFullInvestigation}
            disabled={isLoading}
            className="bg-[#222222] hover:bg-black text-white px-5 py-2 rounded-lg font-bold text-sm transition-colors disabled:opacity-50 shadow-sm flex items-center gap-2"
          >
            {isLoading ? <BrainCircuit className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {isLoading ? "Analyzing..." : "Run Analysis"}
          </button>
        </div>
      </header>

      {/* Workspace Layout */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Sidebar (Navigation) */}
        <aside className="w-64 bg-white border-r border-[#ebebeb] hidden md:flex flex-col py-6">
          <div className="px-6 mb-8">
            <p className="text-[11px] font-bold text-[#aaaaaa] uppercase tracking-wider mb-4">Workspace</p>
            <nav className="space-y-1">
              <button onClick={() => setActiveView("investigation")} className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg ${activeView === 'investigation' ? 'bg-[#f7f7f7] text-[#222222]' : 'text-[#6a6a6a] hover:bg-[#f7f7f7]'}`}><Activity className="h-4 w-4" /> Investigation</button>
              <button onClick={() => setActiveView("scenario")} className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg ${activeView === 'scenario' ? 'bg-[#f7f7f7] text-[#222222]' : 'text-[#6a6a6a] hover:bg-[#f7f7f7]'}`}><BarChart className="h-4 w-4" /> Scenario Lab</button>
              <button onClick={() => setActiveView("reports")} className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg ${activeView === 'reports' ? 'bg-[#f7f7f7] text-[#222222]' : 'text-[#6a6a6a] hover:bg-[#f7f7f7]'}`}><FileText className="h-4 w-4" /> Reports</button>
            </nav>
          </div>
        </aside>

        {/* Center Main Workspace */}
        <main className="flex-1 overflow-y-auto bg-[#fcfcfc] p-8 pb-32">
          <div className="max-w-5xl mx-auto space-y-12">
            
            {/* Replay Controls (Only show if investigation is complete) */}
            {plannerNotebook.length > 0 && (
              <ReplayControls 
                isReplaying={isReplaying}
                setIsReplaying={setIsReplaying}
                replayStep={replayStep}
                setReplayStep={setReplayStep}
                maxSteps={plannerNotebook.length}
              />
            )}
            
            {activeView === "scenario" && (
              <div className="space-y-8">
                <h2 className="text-2xl font-bold text-[#222222]">Interactive Scenario Lab</h2>
                <p className="text-[#6a6a6a]">Adjust base assumptions to instantly project alternative business impact without re-running the LLM planner.</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                   <Card className="bg-white border-[#dddddd]">
                     <CardContent className="p-6">
                       <h3 className="font-bold text-[#222222] mb-4">Base Expected Frequency</h3>
                       <div className="space-y-3">
                         <button onClick={async () => {
                           const res = await axios.post("http://localhost:8000/api/scenario/analyze", { overrides: { expected_frequency_multiplier: 1.1 }})
                           setBusinessImpact(res.data.business_impact)
                         }} className="w-full bg-[#f7f7f7] hover:bg-[#ebebeb] px-4 py-3 rounded-xl flex justify-between font-medium">
                           <span>Shift +10%</span>
                         </button>
                         <button onClick={async () => {
                           const res = await axios.post("http://localhost:8000/api/scenario/analyze", { overrides: { expected_frequency_multiplier: 0.9 }})
                           setBusinessImpact(res.data.business_impact)
                         }} className="w-full bg-[#f7f7f7] hover:bg-[#ebebeb] px-4 py-3 rounded-xl flex justify-between font-medium">
                           <span>Shift -10%</span>
                         </button>
                         <button onClick={async () => {
                           const res = await axios.post("http://localhost:8000/api/scenario/analyze", { overrides: { expected_frequency_multiplier: 1.0 }})
                           setBusinessImpact(res.data.business_impact)
                         }} className="w-full bg-white border border-[#dddddd] hover:bg-[#f7f7f7] px-4 py-3 rounded-xl flex justify-between font-medium">
                           <span>Reset to Baseline</span>
                         </button>
                       </div>
                     </CardContent>
                   </Card>
                   
                   {businessImpact && (
                     <Card className="bg-[#fff0f2] border-[#ff385c]">
                       <CardContent className="p-6">
                         <h3 className="font-bold text-[#ff385c] mb-4">Projected Live Impact</h3>
                         <div className="space-y-4">
                           <div>
                             <p className="text-xs uppercase font-bold text-[#ff385c]/70">Relative Drift</p>
                             <p className="text-2xl font-bold text-[#222222]">{(businessImpact.drift_percentage * 100).toFixed(2)}%</p>
                           </div>
                           <div>
                             <p className="text-xs uppercase font-bold text-[#ff385c]/70">Additional Claims</p>
                             <p className="text-2xl font-bold text-[#222222]">+{businessImpact.additional_claims?.toLocaleString()}</p>
                           </div>
                         </div>
                       </CardContent>
                     </Card>
                   )}
                </div>
              </div>
            )}

            {activeView === "compare" && (
              <ComparisonWorkspace />
            )}
            
            {activeView === "reports" && (
              <div className="space-y-8">
                <div className="flex justify-between items-center">
                   <h2 className="text-2xl font-bold text-[#222222]">Live Report Preview</h2>
                   <button onClick={downloadPdfReport} className="bg-[#137333] hover:bg-green-700 text-white px-5 py-2.5 rounded-lg font-bold text-sm transition-colors shadow-sm flex items-center gap-2">
                     <FileText className="h-4 w-4" /> Export Enterprise PDF
                   </button>
                </div>
                <p className="text-[#6a6a6a]">Review the investigation layout before exporting to a branded, deterministic PDF.</p>
                <div className="bg-white border border-[#dddddd] rounded-xl p-10 shadow-sm space-y-8">
                   <div>
                     <h3 className="text-xl font-bold text-[#222222] border-b pb-2 mb-4">Executive Summary</h3>
                     <p className="text-sm text-[#222222] font-bold">Risk Level: <span className={businessImpact?.risk_level === 'High' ? 'text-[#ff385c]' : 'text-[#fbbc04]'}>{businessImpact?.risk_level || 'Unknown'}</span></p>
                     <p className="text-sm text-[#222222] font-bold">Unexpected Claims: +{businessImpact?.additional_claims?.toLocaleString()}</p>
                   </div>
                   <div>
                     <h3 className="text-xl font-bold text-[#222222] border-b pb-2 mb-4">Event Inference</h3>
                     <p className="text-sm text-[#6a6a6a]">{eventReconstruction || "No inference available."}</p>
                   </div>
                   <div>
                     <h3 className="text-xl font-bold text-[#222222] border-b pb-2 mb-4">Decision Support</h3>
                     {decisionOptions?.map((opt: any, i: number) => (
                       <div key={i} className="mb-4">
                         <p className="font-bold text-sm">{opt.possible_action} ({opt.suggested_priority} Priority)</p>
                         <p className="text-sm text-[#6a6a6a]">Benefits: {opt.benefits}</p>
                         <p className="text-sm text-[#6a6a6a]">Risks: {opt.risks}</p>
                       </div>
                     ))}
                   </div>
                </div>
              </div>
            )}
            
            {activeView === "investigation" && (
              <>
                <ProgressTimeline />
            <ConfidenceBanner />
            
            {!investigationTree && !isLoading && (
              <div className="mt-20 text-center">
                <BrainCircuit className="h-16 w-16 text-[#dddddd] mx-auto mb-6" />
                <h2 className="text-2xl font-bold text-[#222222]">Ready to Investigate</h2>
                <p className="text-[#6a6a6a] mt-2 mb-8 max-w-md mx-auto">Upload a dataset and click Run Analysis to instruct the AI to autonomously identify anomalies and root causes.</p>
              </div>
            )}
            
            {isLoading && (
              <div className="mt-20 text-center">
                <BrainCircuit className="h-16 w-16 text-[#ff385c] animate-pulse mx-auto mb-6" />
                <h2 className="text-2xl font-bold text-[#222222]">AI Analyst is working...</h2>
                <p className="text-[#6a6a6a] mt-2">Evaluating portfolio segments and simulating business impact.</p>
              </div>
            )}

            {!isLoading && investigationTree && (
              <div className="space-y-16">
                
                {/* 1. Event Reconstruction */}
                <section>
                  <h2 className="text-2xl font-bold text-[#222222] mb-6">AI Event Inference</h2>
                  <div className="bg-white p-8 rounded-2xl border border-[#dddddd] shadow-sm flex gap-6 items-start">
                    <div className="bg-[#fff0f2] p-4 rounded-xl shrink-0">
                      <BrainCircuit className="h-8 w-8 text-[#ff385c]" />
                    </div>
                    <div>
                      <p className="text-[18px] text-[#222222] leading-relaxed font-medium">
                        {eventReconstruction || "The evidence suggests a latent shift in claims experience within this demographic segment."}
                      </p>
                      <button onClick={() => setActiveExplainability({type: 'event'})} className="mt-4 text-[#ff385c] font-bold text-sm hover:underline">
                        View Statistical Evidence &rarr;
                      </button>
                    </div>
                  </div>
                </section>

                {/* 2. Planner Notebook */}
                {replayStep > 0 && (
                  <section>
                    <h2 className="text-2xl font-bold text-[#222222] mb-6 flex items-center gap-2">
                      <BrainCircuit className="h-6 w-6 text-[#ff385c]" />
                      AI Analyst Notebook
                    </h2>
                    <div className="relative border-l-2 border-[#ebebeb] ml-4 space-y-8 pl-8">
                      {plannerNotebook.slice(0, replayStep).map((entry: any, index: number) => (
                        <div key={index} className="relative cursor-pointer group" onClick={() => setActiveExplainability({type: 'planner_step', step: entry})}>
                          <div className="absolute -left-[41px] top-0 w-6 h-6 bg-[#ff385c] rounded-full border-4 border-white flex items-center justify-center text-[10px] text-white font-bold group-hover:scale-110 transition-transform">
                            {index + 1}
                          </div>
                          <div className="bg-white p-5 rounded-xl border border-[#dddddd] shadow-sm group-hover:border-[#ff385c] transition-colors">
                            <div className="flex justify-between items-start">
                              <div>
                                <p className="font-bold text-sm text-[#222222] mb-2">{entry.observation}</p>
                                <p className="text-sm text-[#6a6a6a]">{entry.hypothesis}</p>
                              </div>
                              <button className="text-xs font-bold text-[#ff385c] opacity-0 group-hover:opacity-100 transition-opacity">View Evidence &rarr;</button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* 3. Business Impact */}
                <section>
                  <h2 className="text-2xl font-bold text-[#222222] mb-6">Business Impact</h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card className="bg-white shadow-sm border-[#dddddd] md:col-span-1">
                      <CardHeader className="pb-2"><CardTitle className="text-sm text-[#6a6a6a] uppercase tracking-wide">Expected vs Actual</CardTitle></CardHeader>
                      <CardContent>
                        <div className="flex items-end gap-2 mb-1">
                          <p className="text-3xl font-bold text-[#ff385c]">
                            {businessImpact?.observed_frequency !== undefined ? (businessImpact.observed_frequency * 100).toFixed(2) + '%' : 'N/A'}
                          </p>
                        </div>
                        <p className="text-sm text-[#6a6a6a]">Expected: {businessImpact?.expected_frequency !== undefined ? (businessImpact.expected_frequency * 100).toFixed(2) + '%' : 'N/A'}</p>
                        <div className="mt-6 pt-6 border-t border-[#ebebeb]">
                           <p className="text-[10px] uppercase font-bold text-[#aaaaaa] mb-1">Unexpected Claims</p>
                           <p className="text-xl font-bold text-[#222222]">+{businessImpact?.additional_claims?.toLocaleString() || 0}</p>
                        </div>
                        <div className="mt-4">
                           <p className="text-[10px] uppercase font-bold text-[#aaaaaa] mb-1">Affected Exposure</p>
                           <p className="text-xl font-bold text-[#222222]">{businessImpact?.affected_policies_percentage !== undefined ? (businessImpact.affected_policies_percentage * 100).toFixed(1) + '%' : 'N/A'}</p>
                        </div>
                      </CardContent>
                    </Card>
                    <Card className="bg-white shadow-sm border-[#dddddd] md:col-span-2">
                      <CardHeader className="pb-2 border-b border-[#ebebeb]">
                         <CardTitle className="text-sm text-[#222222] font-bold">Relative Drift Trend</CardTitle>
                      </CardHeader>
                      <CardContent>
                         <DriftTrendChart />
                      </CardContent>
                    </Card>
                  </div>
                </section>

                {/* 3.5 Root Cause Intelligence Center */}
                {explainabilityReport && replayStep >= plannerNotebook.length && (
                  <RootCausePanel 
                    primaryRootCause={primaryRootCause || "Unknown"}
                    explainabilityReport={explainabilityReport}
                    businessImpact={businessImpact}
                    tree={investigationTree}
                  />
                )}

                {/* 4. Investigation Evidence */}
                {replayStep >= plannerNotebook.length && (
                  <section>
                    <h2 className="text-2xl font-bold text-[#222222] mb-6">Investigation Evidence</h2>
                    <div className="bg-white p-6 rounded-2xl border border-[#dddddd] shadow-sm">
                       <p className="text-[#6a6a6a] text-sm mb-6">The AI recursively analyzed the portfolio to isolate the primary driver of the drift.</p>
                       <TreeNode node={investigationTree} />
                    </div>
                  </section>
                )}

                {/* 5. Decision Support Matrix */}
                {replayStep >= plannerNotebook.length - 1 && decisionOptions.length > 0 && (
                  <section>
                    <div className="flex justify-between items-end mb-6">
                      <h2 className="text-2xl font-bold text-[#222222]">Decision Intelligence</h2>
                    <button className="text-[#6a6a6a] text-sm font-semibold hover:text-[#222222]">Filter & Sort</button>
                  </div>
                  <div className="space-y-4">
                    {decisionOptions?.map((opt: any, i: number) => (
                      <div key={i} className="bg-white border border-[#dddddd] rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden cursor-pointer" onClick={() => setActiveExplainability({type: 'decision', data: opt})}>
                        <div className="flex flex-col md:flex-row">
                          <div className="md:w-1/3 bg-[#f7f7f7] p-6 border-b md:border-b-0 md:border-r border-[#ebebeb]">
                            <Badge className={`mb-3 ${opt.suggested_priority === 'High' ? 'bg-[#ff385c]' : 'bg-[#137333]'}`}>{opt.suggested_priority} Priority</Badge>
                            <h3 className="text-lg font-bold text-[#222222]">{opt.possible_action}</h3>
                          </div>
                          <div className="md:w-2/3 p-6 grid grid-cols-2 gap-6">
                            <div>
                              <p className="text-xs font-bold text-[#137333] uppercase tracking-wider mb-2">Benefits</p>
                              <p className="text-sm text-[#222222]">{opt.benefits}</p>
                            </div>
                            <div>
                              <p className="text-xs font-bold text-[#ff385c] uppercase tracking-wider mb-2">Risks</p>
                              <p className="text-sm text-[#222222]">{opt.risks}</p>
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

        {/* Right Sidebar (Context Panel) */}
        <aside className="w-80 bg-[#f7f7f7] border-l border-[#ebebeb] hidden lg:flex flex-col overflow-y-auto">
          <div className="p-6 border-b border-[#ebebeb]">
            <h3 className="text-sm font-bold text-[#222222] uppercase tracking-wider mb-4">Investigation Context</h3>
            
            <div className="space-y-4">
              <div>
                <p className="text-xs text-[#6a6a6a] mb-1">Dataset</p>
                <div className="bg-white border border-[#dddddd] px-3 py-2 rounded text-sm text-[#222222] font-medium truncate">
                  {dataset}
                </div>
              </div>
              
              {drift && (
                <div>
                  <p className="text-xs text-[#6a6a6a] mb-1">Z-Score (Confidence)</p>
                  <div className={`px-3 py-2 rounded text-sm font-bold ${Math.abs(drift.z_score) > 2 ? 'bg-[#fff0f2] text-[#ff385c]' : 'bg-[#e6f4ea] text-[#137333]'}`}>
                    {Math.abs(drift.z_score).toFixed(2)}σ
                  </div>
                </div>
              )}
            </div>
          </div>
          
                {/* Explainability Panel (when active) */}
          <AnimatePresence>
            {activeExplainability && (
              <motion.div 
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="fixed top-0 right-0 bottom-0 w-[500px] bg-white border-l border-[#dddddd] shadow-2xl z-50 flex flex-col overflow-hidden"
              >
                <div className="flex justify-between items-center p-6 border-b border-[#dddddd] bg-[#fafafa]">
                  <h3 className="font-bold text-[#222222] flex items-center gap-2">
                    <Search className="h-5 w-5 text-[#ff385c]" /> Evidence Explorer
                  </h3>
                  <button onClick={() => setActiveExplainability(null)} className="p-2 bg-[#ebebeb] hover:bg-[#dddddd] rounded-full transition-colors"><X className="h-4 w-4 text-[#222222]" /></button>
                </div>
                
                <div className="flex-1 overflow-y-auto p-6 space-y-8">
                  {activeExplainability.type === 'event' && (
                    <div className="space-y-6">
                      <div className="bg-[#fff0f2] border border-[#ffb3c0] rounded-xl p-6">
                        <p className="text-sm font-bold text-[#ff385c] uppercase tracking-wider mb-2">Statistical Divergence</p>
                        <div className="flex items-end gap-3">
                          <p className="text-4xl font-bold text-[#ff385c]">
                            {businessImpact?.observed_frequency !== undefined ? (businessImpact.observed_frequency * 100).toFixed(2) + '%' : 'N/A'}
                          </p>
                          <p className="text-sm text-[#ff385c] font-medium pb-1">Actual</p>
                        </div>
                        <div className="mt-4 flex justify-between items-center pt-4 border-t border-[#ffb3c0]">
                          <span className="text-[#ff385c] font-medium text-sm">Expected Baseline</span>
                          <span className="font-bold text-[#ff385c] text-lg">{businessImpact?.expected_frequency !== undefined ? (businessImpact.expected_frequency * 100).toFixed(2) + '%' : 'N/A'}</span>
                        </div>
                      </div>
                      
                      <div className="bg-white border border-[#dddddd] rounded-xl p-6 shadow-sm space-y-4">
                        <h4 className="font-bold text-[#222222]">Z-Score Significance</h4>
                        <div className="flex items-center gap-4">
                          <div className={`px-4 py-2 rounded-lg text-lg font-bold ${Math.abs(drift?.z_score || 0) > 2 ? 'bg-[#fff0f2] text-[#ff385c]' : 'bg-[#e6f4ea] text-[#137333]'}`}>
                            {Math.abs(drift?.z_score || 0).toFixed(2)}σ
                          </div>
                          <p className="text-sm text-[#6a6a6a]">A z-score &gt; 1.96 indicates 95% statistical confidence that this drift is not due to random noise.</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeExplainability.type === 'planner_step' && (
                    <div className="space-y-6">
                      <div className="bg-[#f7f7f7] p-5 rounded-xl border border-[#dddddd]">
                        <p className="text-[10px] uppercase font-bold text-[#aaaaaa] tracking-wider mb-1">AI Hypothesis</p>
                        <p className="font-medium text-[#222222]">{activeExplainability.step.hypothesis}</p>
                      </div>

                      <div className="bg-[#222222] p-5 rounded-xl text-white font-mono text-sm shadow-inner overflow-x-auto relative mt-4">
                        <p className="text-[#aaaaaa] mb-2">// Executed Action</p>
                        <p className="text-[#4ade80]">{">>"} {activeExplainability.step.decision}</p>
                      </div>

                      <div className="space-y-3">
                        <p className="font-bold text-sm text-[#222222] uppercase tracking-wider">Internal Graph State</p>
                        <div className="bg-white border border-[#dddddd] rounded-xl p-4 overflow-x-auto shadow-sm max-h-[300px] overflow-y-auto">
                          <pre className="text-xs text-[#6a6a6a]">
                            {JSON.stringify(investigationTree || drift || businessImpact, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeExplainability.type === 'node' && (
                    <div className="space-y-6">
                      <div className="bg-white p-5 rounded-xl border border-[#dddddd] shadow-sm">
                        <p className="text-[10px] uppercase font-bold text-[#aaaaaa] tracking-wider mb-1">Segment Path</p>
                        <p className="font-medium text-[#222222] break-words">{activeExplainability.data.name}</p>
                      </div>

                      {activeExplainability.data.split_feature && (
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-[#f7f7f7] p-4 rounded-xl border border-[#dddddd]">
                            <p className="text-[10px] uppercase font-bold text-[#aaaaaa] tracking-wider mb-1">Split Feature</p>
                            <p className="font-bold text-[#222222]">{activeExplainability.data.split_feature}</p>
                          </div>
                          <div className="bg-[#f7f7f7] p-4 rounded-xl border border-[#dddddd]">
                            <p className="text-[10px] uppercase font-bold text-[#aaaaaa] tracking-wider mb-1">Statistical Confidence</p>
                            <p className="font-bold text-[#137333]">{(activeExplainability.data.confidence * 100).toFixed(1)}%</p>
                          </div>
                        </div>
                      )}
                      
                      <div className="bg-white border border-[#dddddd] rounded-xl p-5 shadow-sm space-y-3">
                        <p className="font-bold text-sm text-[#222222]">Drift Metrics</p>
                        <div className="flex justify-between items-center text-sm">
                          <span className="text-[#6a6a6a]">Exposure</span>
                          <span className="font-medium">{activeExplainability.data.exposure?.toLocaleString() || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                          <span className="text-[#6a6a6a]">Actual Frequency</span>
                          <span className="font-medium">{(activeExplainability.data.actual_frequency * 100).toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                          <span className="text-[#6a6a6a]">Expected Frequency</span>
                          <span className="font-medium">{(activeExplainability.data.expected_frequency * 100).toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between items-center pt-2 border-t border-[#ebebeb]">
                          <span className="font-bold text-[#222222]">Segment Drift</span>
                          <span className={`font-bold ${activeExplainability.data.drift > 0 ? 'text-[#ff385c]' : 'text-[#137333]'}`}>
                            {(activeExplainability.data.drift * 100).toFixed(2)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeExplainability.type === 'decision' && (
                    <div className="space-y-4">
                      <div className="bg-[#f7f7f7] p-6 rounded-xl border border-[#dddddd]">
                        <p className="font-bold text-[#222222] mb-4">Supporting Evidence</p>
                        <ul className="space-y-3">
                          {activeExplainability.data.supporting_evidence.map((ev: string, i: number) => (
                            <li key={i} className="flex gap-3 text-sm text-[#444444]">
                              <div className="mt-0.5 min-w-1.5 w-1.5 h-1.5 rounded-full bg-[#ff385c]" />
                              {ev}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
        </aside>

      </div>
      
      {/* Docked AI Copilot */}
      <AnimatePresence>
        {isCopilotOpen ? (
          <motion.div 
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed bottom-0 left-0 right-0 md:left-64 md:right-80 h-[50vh] bg-white border-t border-[#ebebeb] shadow-[0_-10px_40px_rgba(0,0,0,0.1)] rounded-t-2xl z-40 flex flex-col"
          >
            <div className="p-4 border-b border-[#ebebeb] flex justify-between items-center cursor-pointer" onClick={() => setIsCopilotOpen(false)}>
              <div className="flex items-center gap-3">
                <div className="bg-[#222222] p-1.5 rounded-md"><MessageSquare className="h-4 w-4 text-white" /></div>
                <h3 className="font-bold text-[#222222]">AI Copilot Session</h3>
              </div>
              <X className="h-5 w-5 text-[#6a6a6a]" />
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#fafafa]">
              {copilotMessages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center">
                  <div className="bg-[#ff385c]/10 p-4 rounded-full mb-4">
                    <MessageSquare className="h-8 w-8 text-[#ff385c]" />
                  </div>
                  <h3 className="text-xl font-bold text-[#222222] mb-2">Ask the Copilot</h3>
                  <p className="text-[#6a6a6a] text-center max-w-sm">I have access to the full context of this investigation. Ask me about the root causes, the impact, or what we should do next.</p>
                </div>
              ) : (
                copilotMessages.map((msg, i) => (
                  <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                    {msg.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-full bg-[#ff385c] flex items-center justify-center shrink-0">
                        <span className="text-white text-xs font-bold">AI</span>
                      </div>
                    )}
                    <div className={`p-4 rounded-2xl max-w-3xl ${msg.role === 'user' ? 'bg-[#f7f7f7] border border-[#dddddd] text-[#222222]' : 'bg-white border border-[#ebebeb] shadow-sm text-[#222222]'}`}>
                      {msg.content}
                    </div>
                  </div>
                ))
              )}
            </div>
            
            <div className="p-4 border-t border-[#ebebeb] bg-white">
              <div className="relative max-w-5xl mx-auto">
                <input 
                  type="text" 
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') sendChatMessage() }}
                  placeholder="Ask a question about this investigation..."
                  className="w-full bg-[#f7f7f7] border border-[#dddddd] rounded-full pl-6 pr-12 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#ff385c]/20"
                />
                <button onClick={sendChatMessage} className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-[#ff385c] text-white rounded-full hover:bg-[#e03150] transition-colors">
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.button
            initial={{ y: 100 }}
            animate={{ y: 0 }}
            onClick={() => setIsCopilotOpen(true)}
            className="fixed bottom-6 left-1/2 md:left-[calc(50%-1rem)] transform -translate-x-1/2 bg-[#222222] text-white px-6 py-3 rounded-full shadow-2xl font-bold text-sm flex items-center gap-3 hover:bg-black transition-colors z-30 border border-[#333333]"
          >
            <MessageSquare className="h-4 w-4" />
            Open AI Copilot
          </motion.button>
        )}
      </AnimatePresence>

    </div>
  )
}
