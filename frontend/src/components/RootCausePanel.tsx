import React from 'react'
import { Badge } from "@/components/ui/badge"
import { motion } from "framer-motion"
import { BrainCircuit, ShieldCheck, GitMerge } from "lucide-react"
import { useStore } from "@/store/store"
import { EnterpriseCard, EnterpriseCardHeader, EnterpriseCardTitle, EnterpriseCardContent } from "@/components/ui/EnterpriseCard"

interface RootCausePanelProps {
  primaryRootCause: string;
  explainabilityReport: any;
  businessImpact: any;
  tree: any;
}

export default function RootCausePanel({ primaryRootCause, explainabilityReport, businessImpact, tree }: RootCausePanelProps) {
  const { decisionOptions } = useStore()
  
  if (!explainabilityReport) return null;

  const score = explainabilityReport.overall_score || 0;
  const factors = explainabilityReport.factors || [];
  const explanation = explainabilityReport.explanation_text || "No AI explanation available.";

  const isCombined = businessImpact?.observed_claim_cost !== undefined;
  const isSeverity = businessImpact?.observed_severity !== undefined;

  const statisticalPattern = isCombined 
    ? (businessImpact.deterioration_pattern || "Mixed Deterioration")
    : (isSeverity ? "Severity-Led Deterioration" : "Frequency-Led Deterioration");

  const primarySegment = businessImpact?.most_impacted_portfolio || "Root Portfolio";
  const hasCrossEngineAlignment = decisionOptions?.some(opt => opt.cross_engine_alignment) || false;

  let statisticalConfidence = "N/A";
  if (isCombined) statisticalConfidence = "Deterministic Actuarial Reconciliation";
  else if (isSeverity) statisticalConfidence = "95% Bootstrap Confidence Interval";
  else statisticalConfidence = "Benjamini-Hochberg FDR Control (q < 0.05)";

  const businessImpactText = isCombined
    ? `₹${businessImpact.excess_claim_cost?.toLocaleString(undefined, {maximumFractionDigits: 0})}`
    : `₹${businessImpact.excess_cost?.toLocaleString(undefined, {maximumFractionDigits: 0}) || '0'}`;

  const getScoreColor = (s: number) => {
    if (s >= 80) return "text-accent-green bg-accent-green-soft";
    if (s >= 50) return "text-accent-yellow bg-accent-yellow-soft";
    return "text-accent-red bg-accent-red-soft";
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8"
    >
      <EnterpriseCard elevated>
        {/* Header */}
        <EnterpriseCardHeader className="flex-row items-center justify-between">
          <div>
            <EnterpriseCardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-accent-green" />
              Root Cause Intelligence Center
            </EnterpriseCardTitle>
            <p className="text-body-sm text-mute mt-1">Deterministic analysis and mathematical justification of the primary anomaly driver.</p>
          </div>
          <div className="text-right">
            <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-1">Explainability Score</p>
            <div className={`inline-flex px-3 py-1 rounded-[var(--radius-md)] border border-hairline font-mono font-bold text-heading-md ${getScoreColor(score)}`}>
              {score}/100
            </div>
          </div>
        </EnterpriseCardHeader>

        {/* Content */}
        <EnterpriseCardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            
            {/* Left column */}
            <div className="flex flex-col gap-3">
              <div className="bg-surface-elevated p-4 rounded-[var(--radius-lg)] border border-hairline">
                <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-2 flex items-center gap-1">
                  <GitMerge className="h-3 w-3" /> Statistical Pattern
                </p>
                <p className="text-body-sm-strong text-ink mb-2">{statisticalPattern}</p>
                <Badge className="bg-accent-red-soft text-accent-red border-0 shadow-none uppercase text-[10px] tracking-wider">
                  {isCombined ? "Combined Analysis" : (isSeverity ? "Severity Gate" : "Frequency Gate")}
                </Badge>
              </div>
              
              <div className="bg-surface-elevated p-4 rounded-[var(--radius-lg)] border border-hairline">
                <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-1">Primary Segment</p>
                <p className="text-body-sm-strong text-ink truncate" title={primarySegment}>{primarySegment}</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="bg-surface-elevated p-4 rounded-[var(--radius-lg)] border border-hairline">
                  <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-1">Business Impact</p>
                  <p className="text-body-sm-strong text-ink font-mono tabular-nums">{businessImpactText}</p>
                </div>
                <div className="bg-surface-elevated p-4 rounded-[var(--radius-lg)] border border-hairline">
                  <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-1">Alignment</p>
                  <p className={`text-caption-sm font-medium ${hasCrossEngineAlignment ? 'text-accent-green' : 'text-mute'}`}>
                    {hasCrossEngineAlignment ? "Cross-Engine" : "Standalone"}
                  </p>
                </div>
              </div>

              <div className="bg-surface-elevated p-4 rounded-[var(--radius-lg)] border border-hairline">
                <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-1">Statistical Confidence</p>
                <p className="text-caption-md text-body font-medium">{statisticalConfidence}</p>
              </div>
            </div>

            {/* Right column */}
            <div className="md:col-span-2 flex flex-col gap-3">
              <div className="bg-surface-elevated p-5 rounded-[var(--radius-lg)] border border-hairline flex-1">
                <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-3 flex items-center gap-1">
                  <BrainCircuit className="h-3 w-3" /> Root Cause Hypothesis
                </p>
                <div className="text-body-sm text-body leading-relaxed space-y-2">
                  {explanation.split('. ').map((sentence: string, i: number) => (
                    <p key={i}>{sentence}{sentence.endsWith('.') ? '' : '.'}</p>
                  ))}
                </div>
              </div>
              
              {factors.length > 0 && (
                <div className="grid grid-cols-3 gap-3">
                  {factors.map((f: any, i: number) => (
                    <div key={i} className="bg-surface-elevated p-3 rounded-[var(--radius-lg)] border border-hairline">
                      <div className="flex justify-between items-center mb-1">
                        <p className="text-caption-sm text-ash uppercase tracking-wider font-medium truncate" title={f.name}>{f.name}</p>
                        <span className={`h-2 w-2 rounded-full shrink-0 ${f.status === 'Strong' ? 'bg-accent-green' : f.status === 'Moderate' ? 'bg-accent-yellow' : 'bg-accent-red'}`} />
                      </div>
                      <p className="text-caption-sm text-body mt-2 line-clamp-2" title={f.desc}>{f.desc}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        </EnterpriseCardContent>
      </EnterpriseCard>
    </motion.div>
  )
}
