import React, { useEffect, useState } from "react"
import { EnterpriseCard, EnterpriseCardContent } from "@/components/ui/EnterpriseCard"
import { motion } from "framer-motion"
import { API_BASE_URL } from "@/lib/api"

interface KPICardProps {
  title: string
  value: string | number
  subtitle?: string
  trend?: string
  isCurrency?: boolean
  isPercentage?: boolean
  delay?: number
}

function KPICard({ title, value, subtitle, trend, isCurrency, isPercentage, delay = 0 }: KPICardProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="h-full"
    >
      <EnterpriseCard className="h-full">
        <EnterpriseCardContent className="p-5 flex flex-col justify-center h-full min-h-[120px]">
          <span className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-3">{title}</span>
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className="text-heading-xl text-ink tabular-nums">
              {isCurrency && "₹"}
              {typeof value === 'number' ? value.toLocaleString() : value}
              {isPercentage && "%"}
            </span>
            {trend && (
              <span className={`text-caption-md font-medium ${trend.startsWith('+') ? 'text-accent-red' : 'text-accent-green'}`}>
                {trend}
              </span>
            )}
          </div>
          {subtitle && <span className="text-caption-sm text-mute mt-1.5">{subtitle}</span>}
        </EnterpriseCardContent>
      </EnterpriseCard>
    </motion.div>
  )
}

export default function PortfolioKPIRow() {
  const [metrics, setMetrics] = useState<any>(null)
  
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/drift`)
        if (res.ok) {
          const data = await res.json()
          setMetrics(data)
        }
      } catch (e) {
        console.error("Failed to load metrics")
      }
    }
    fetchMetrics()
  }, [])

  if (!metrics) {
    return (
      <div className="grid grid-cols-1 gap-4">
        <EnterpriseCard>
          <div className="p-5 text-center text-body-sm text-mute">
            No portfolio metrics available. Run a dataset to populate KPIs.
          </div>
        </EnterpriseCard>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      <KPICard title="Expected Claims" value={metrics.expected_claims?.toFixed(0) || "—"} delay={0} />
      <KPICard title="Actual Claims" value={metrics.actual_claims?.toFixed(0) || "—"} delay={0.05} />
      <KPICard title="Observed Freq" value={(metrics.observed_frequency * 100)?.toFixed(2) || "—"} isPercentage delay={0.1} />
      <KPICard title="Drift" value={metrics.drift_percentage?.toFixed(2) || "—"} isPercentage trend={metrics.requires_investigation ? "Requires Investigation" : "Stable"} delay={0.15} />
      <KPICard title="Quality Score" value="100" isPercentage delay={0.2} />
    </div>
  )
}
