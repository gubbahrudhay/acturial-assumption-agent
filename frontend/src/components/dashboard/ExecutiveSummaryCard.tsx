import React from "react"
import { Activity, AlertTriangle, CheckCircle, TrendingUp, Target, BrainCircuit } from "lucide-react"
import { EnterpriseCard, EnterpriseCardHeader, EnterpriseCardTitle, EnterpriseCardContent } from "@/components/ui/EnterpriseCard"

export default function ExecutiveSummaryCard({ analytics, dataset }: { analytics: any, dataset: string }) {
  const status = analytics?.recurring_issues?.length > 0 ? "Monitor" : "Healthy"
  const isHealthy = status === "Healthy"
  
  const rootCause = analytics?.recurring_issues?.[0]?.root_cause || "No systemic drift"
  const freqDrift = analytics?.frequency_drift ?? "+0.0%"
  const sevDrift = analytics?.severity_drift ?? "+0.0%"
  const confidence = analytics?.confidence ?? "98%"
  
  return (
    <EnterpriseCard elevated>
      <EnterpriseCardHeader className="flex-row items-center justify-between">
        <EnterpriseCardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-accent-blue" />
          Portfolio Health Overview
        </EnterpriseCardTitle>
        <div className={`px-3 py-1 rounded-[var(--radius-sm)] text-caption-md font-medium flex items-center gap-1.5 ${isHealthy ? 'bg-accent-green-soft text-accent-green' : 'bg-accent-yellow-soft text-accent-yellow'}`}>
          {isHealthy ? <CheckCircle className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
          {status}
        </div>
      </EnterpriseCardHeader>
      <EnterpriseCardContent>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          
          <div className="flex flex-col gap-1.5">
            <span className="text-caption-sm text-ash uppercase tracking-wider font-medium flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5" />
              Primary Root Cause
            </span>
            <span className="text-heading-sm text-ink">{rootCause}</span>
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-caption-sm text-ash uppercase tracking-wider font-medium flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5" />
              Frequency Drift
            </span>
            <span className="text-heading-sm text-accent-red tabular-nums">{freqDrift}</span>
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-caption-sm text-ash uppercase tracking-wider font-medium flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5" />
              Severity Drift
            </span>
            <span className="text-heading-sm text-accent-red tabular-nums">{sevDrift}</span>
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-caption-sm text-ash uppercase tracking-wider font-medium flex items-center gap-1.5">
              <BrainCircuit className="w-3.5 h-3.5" />
              AI Confidence
            </span>
            <span className="text-heading-sm text-ink tabular-nums">{confidence}</span>
          </div>
          
        </div>
        
        <div className="mt-6 pt-5 border-t border-hairline grid grid-cols-1 sm:grid-cols-3 gap-4">
           <div className="flex flex-col gap-0.5">
             <span className="text-caption-sm text-ash uppercase tracking-wider font-medium">Active Dataset</span>
             <span className="text-body-sm text-body">{dataset}</span>
           </div>
           <div className="flex flex-col gap-0.5">
             <span className="text-caption-sm text-ash uppercase tracking-wider font-medium">Investigation Trigger</span>
             <span className="text-body-sm text-body">Portfolio Gate Exceeded</span>
           </div>
           <div className="flex flex-col gap-0.5">
             <span className="text-caption-sm text-ash uppercase tracking-wider font-medium">Recommended Action</span>
             <span className="text-body-sm text-accent-blue">Review Pricing Multipliers</span>
           </div>
        </div>
      </EnterpriseCardContent>
    </EnterpriseCard>
  )
}
