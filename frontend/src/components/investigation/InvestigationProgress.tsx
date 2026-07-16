import React from "react"
import { CheckCircle2, Circle, Loader2 } from "lucide-react"

export default function InvestigationProgress({ status }: { status: string }) {
  const steps = [
    { id: "start", label: "Dataset" },
    { id: "readiness", label: "Readiness" },
    { id: "frequency", label: "Frequency" },
    { id: "severity", label: "Severity" },
    { id: "combined", label: "Combined" },
    { id: "planner", label: "Planner" },
    { id: "impact", label: "Decision Support" },
    { id: "report", label: "Report" }
  ]

  // A very simplistic way to determine progress index
  const statusIndex = steps.findIndex(s => s.id === status)
  const currentStep = statusIndex >= 0 ? statusIndex : (status === "end" ? steps.length : 0)

  return (
    <div className="w-full py-6 px-4 bg-surface border-b border-hairline z-10 relative">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between relative">
          
          {/* Connecting Line */}
          <div className="absolute left-0 right-0 top-1/2 h-0.5 -translate-y-1/2 bg-hairline z-0 hidden md:block" />
          
          {/* Active Connecting Line */}
          <div 
            className="absolute left-0 top-1/2 h-0.5 -translate-y-1/2 bg-accent-blue z-0 transition-all duration-700 ease-in-out hidden md:block"
            style={{ width: `${Math.min(100, (currentStep / (steps.length - 1)) * 100)}%` }}
          />

          {steps.map((step, idx) => {
            const isCompleted = idx < currentStep
            const isActive = idx === currentStep
            
            return (
              <div key={step.id} className="relative z-10 flex flex-col items-center gap-2 bg-surface px-2">
                {isCompleted ? (
                  <div className="w-6 h-6 rounded-full bg-accent-blue text-white flex items-center justify-center shadow-sm">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                ) : isActive ? (
                  <div className="w-6 h-6 rounded-full bg-accent-blue-soft text-accent-blue border-2 border-accent-blue flex items-center justify-center animate-pulse shadow-sm">
                    <Loader2 className="w-3 h-3 animate-spin" />
                  </div>
                ) : (
                  <div className="w-6 h-6 rounded-full bg-surface-elevated text-ash border-2 border-hairline flex items-center justify-center">
                    <Circle className="w-3 h-3 fill-current opacity-20" />
                  </div>
                )}
                <span className={`text-[10px] font-semibold uppercase tracking-wider hidden md:block ${isActive ? 'text-accent-blue' : isCompleted ? 'text-ink' : 'text-mute'}`}>
                  {step.label}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
