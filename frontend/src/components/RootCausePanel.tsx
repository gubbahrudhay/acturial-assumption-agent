import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { motion } from "framer-motion"
import { BrainCircuit, Activity, BarChart, ShieldCheck, GitMerge } from "lucide-react"

interface RootCausePanelProps {
  primaryRootCause: string;
  explainabilityReport: any;
  businessImpact: any;
  tree: any;
}

export default function RootCausePanel({ primaryRootCause, explainabilityReport, businessImpact, tree }: RootCausePanelProps) {
  if (!explainabilityReport) return null;

  const score = explainabilityReport.overall_score || 0;
  const factors = explainabilityReport.factors || [];
  const explanation = explainabilityReport.explanation_text || "No AI explanation available.";

  const getScoreColor = (s: number) => {
    if (s >= 80) return "text-emerald-400 bg-emerald-400/10 border-emerald-400/20";
    if (s >= 50) return "text-amber-400 bg-amber-400/10 border-amber-400/20";
    return "text-red-400 bg-red-400/10 border-red-400/20";
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8"
    >
      <div className="bg-[#1a1a1a] border border-[#333333] rounded-2xl overflow-hidden shadow-2xl relative">
        {/* Header */}
        <div className="bg-gradient-to-r from-[#222222] to-[#1a1a1a] p-6 border-b border-[#333333] flex justify-between items-center">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <ShieldCheck className="h-5 w-5 text-emerald-400" />
              <h2 className="text-white text-lg font-bold">Root Cause Intelligence Center</h2>
            </div>
            <p className="text-[#aaaaaa] text-sm">Deterministic analysis and mathematical justification of the primary anomaly driver.</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] uppercase font-bold tracking-wider text-[#aaaaaa] mb-1">Explainability Score</p>
            <div className={`inline-flex px-3 py-1 rounded-lg border font-mono font-bold text-xl ${getScoreColor(score)}`}>
              {score}/100
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Main Root Cause Identity */}
          <div className="md:col-span-1 flex flex-col gap-4">
            <div className="bg-[#222222] p-4 rounded-xl border border-[#333333]">
              <p className="text-[10px] uppercase font-bold text-[#aaaaaa] mb-2 flex items-center gap-1">
                <GitMerge className="h-3 w-3" /> Primary Root Cause
              </p>
              <p className="text-white font-bold text-lg mb-2">{primaryRootCause}</p>
              <Badge className="bg-[#ff385c]/10 text-[#ff385c] border-[#ff385c]/20 hover:bg-[#ff385c]/20 shadow-none uppercase text-[10px]">
                High Drift Identified
              </Badge>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-[#222222] p-4 rounded-xl border border-[#333333]">
                <p className="text-[10px] uppercase font-bold text-[#aaaaaa] mb-1">Unexpected Claims</p>
                <p className="text-white font-mono font-bold text-lg">+{businessImpact?.additional_claims?.toLocaleString() || 0}</p>
              </div>
              <div className="bg-[#222222] p-4 rounded-xl border border-[#333333]">
                <p className="text-[10px] uppercase font-bold text-[#aaaaaa] mb-1">Total Exposure</p>
                <p className="text-white font-mono font-bold text-lg">{businessImpact?.affected_policies_percentage !== undefined ? (businessImpact.affected_policies_percentage * 100).toFixed(1) + '%' : 'N/A'}</p>
              </div>
            </div>
          </div>

          {/* AI Interpretation */}
          <div className="md:col-span-2 flex flex-col gap-4">
            <div className="bg-[#222222] p-5 rounded-xl border border-[#333333] flex-1">
              <p className="text-[10px] uppercase font-bold text-[#aaaaaa] mb-3 flex items-center gap-1">
                <BrainCircuit className="h-3 w-3" /> Deterministic Explanation
              </p>
              <div className="text-[#dddddd] text-sm leading-relaxed space-y-2">
                {explanation.split('. ').map((sentence: string, i: number) => (
                  <p key={i}>{sentence}{sentence.endsWith('.') ? '' : '.'}</p>
                ))}
              </div>
            </div>
            
            {/* Factor Breakdown */}
            <div className="grid grid-cols-3 gap-4">
              {factors.map((f: any, i: number) => (
                <div key={i} className="bg-[#222222] p-3 rounded-xl border border-[#333333]">
                  <div className="flex justify-between items-center mb-1">
                    <p className="text-[10px] uppercase font-bold text-[#aaaaaa]">{f.name}</p>
                    <div className={`h-2 w-2 rounded-full ${f.status === 'Strong' ? 'bg-emerald-400' : f.status === 'Moderate' ? 'bg-amber-400' : 'bg-red-400'}`} />
                  </div>
                  <p className="text-white text-xs mt-2 line-clamp-2" title={f.desc}>{f.desc}</p>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </motion.div>
  )
}
