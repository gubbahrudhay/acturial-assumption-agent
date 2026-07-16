import React from "react"
import { EnterpriseCard, EnterpriseCardHeader, EnterpriseCardTitle, EnterpriseCardContent } from "@/components/ui/EnterpriseCard"
import { Clock, FileText, Activity, Database, CheckCircle2 } from "lucide-react"

export default function PortfolioHealthTimeline() {
  const events: any[] = []

  return (
    <EnterpriseCard>
      <EnterpriseCardHeader>
        <EnterpriseCardTitle className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-mute" />
          Recent Activity Timeline
        </EnterpriseCardTitle>
      </EnterpriseCardHeader>
      <EnterpriseCardContent>
        <div className="relative border-l border-hairline ml-3 mt-4 space-y-6 pb-2 min-h-[150px] flex items-center justify-center">
          {events.length === 0 ? (
             <div className="text-center text-body-sm text-mute">
                No activity found for this portfolio.
             </div>
          ) : (
            events.map((event, idx) => {
              const Icon = event.icon || Clock
              return (
                <div key={event.id} className="relative pl-6">
                  <span className={`absolute -left-3 top-1 flex h-6 w-6 items-center justify-center rounded-full ring-4 ring-surface ${event.bg}`}>
                    <Icon className={`h-3 w-3 ${event.color}`} />
                  </span>
                  <div className="flex flex-col">
                    <span className="text-body-sm-strong text-ink">{event.title}</span>
                    <span className="text-caption-sm text-mute mt-0.5">{event.date}</span>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </EnterpriseCardContent>
    </EnterpriseCard>
  )
}
