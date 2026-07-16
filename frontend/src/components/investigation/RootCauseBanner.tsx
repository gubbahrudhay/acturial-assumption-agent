import React from "react"
import { AlertTriangle, AlertCircle, Target, TrendingUp, AlertOctagon } from "lucide-react"

export default function RootCauseBanner({ impact, rootCause, confidence }: any) {
  const isHighRisk = impact?.risk_level === "High"
  
  return (
    <div className={`w-full border-b ${isHighRisk ? 'bg-accent-red-soft border-accent-red-soft' : 'bg-accent-yellow-soft border-accent-yellow-soft'} px-6 py-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 rounded-[var(--radius-lg)] mb-8`}>
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-[var(--radius-md)] mt-1 md:mt-0 ${isHighRisk ? 'bg-accent-red text-white' : 'bg-accent-yellow text-surface'}`}>
          {isHighRisk ? <AlertOctagon className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-caption-sm font-bold uppercase tracking-wider ${isHighRisk ? 'text-accent-red' : 'text-accent-yellow'}`}>
              Primary Root Cause Identified
            </span>
            <span className="px-2 py-0.5 rounded-[var(--radius-sm)] bg-surface text-caption-sm font-medium text-mute border border-hairline">
              Confidence: {confidence || "98%"}
            </span>
          </div>
          <h2 className="text-heading-lg text-ink tracking-tight flex items-center gap-2">
            <Target className="w-5 h-5 text-mute" />
            {rootCause || "Unknown Segment"}
          </h2>
        </div>
      </div>
      
      <div className="flex flex-wrap items-center gap-4 md:gap-8">
        <div className="flex flex-col">
          <span className="text-caption-sm text-ash font-semibold uppercase">Business Impact</span>
          <span className="text-body-sm-strong text-ink">{impact?.risk_level || "Unknown"} Risk</span>
        </div>
        <div className="flex flex-col">
          <span className="text-caption-sm text-ash font-semibold uppercase">Affected Exposure</span>
          <span className="text-body-sm-strong text-ink">{impact?.claim_count || impact?.additional_claims || 0} claims</span>
        </div>
        <div className="flex flex-col">
          <span className="text-caption-sm text-ash font-semibold uppercase">Estimated Excess Cost</span>
          <span className="text-body-sm-strong text-accent-red flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            ₹{(impact?.excess_cost || 0).toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  )
}
