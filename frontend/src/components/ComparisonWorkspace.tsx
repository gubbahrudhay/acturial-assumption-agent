import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { API_BASE_URL } from "@/lib/api"
import { EnterpriseCard, EnterpriseCardHeader, EnterpriseCardTitle, EnterpriseCardContent } from "@/components/ui/EnterpriseCard"
import { GitMerge, CheckCircle2 } from 'lucide-react'

export default function ComparisonWorkspace() {
  const [investigations, setInvestigations] = useState<any[]>([])
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [comparisonData, setComparisonData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const fetchList = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/api/investigations`)
        setInvestigations(res.data.investigations || [])
      } catch (e) {
        console.error("Failed to fetch investigations", e)
      }
    }
    fetchList()
  }, [])

  useEffect(() => {
    const fetchComparison = async () => {
      if (selectedIds.length !== 2) {
        setComparisonData([])
        return
      }
      setLoading(true)
      try {
        const res1 = await axios.get(`${API_BASE_URL}/api/investigation/${selectedIds[0]}`)
        const res2 = await axios.get(`${API_BASE_URL}/api/investigation/${selectedIds[1]}`)
        setComparisonData([res1.data.investigation_state, res2.data.investigation_state])
      } catch (e) {
        console.error("Failed to fetch investigation details", e)
      } finally {
        setLoading(false)
      }
    }
    fetchComparison()
  }, [selectedIds])

  const toggleSelection = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(i => i !== id))
    } else if (selectedIds.length < 2) {
      setSelectedIds([...selectedIds, id])
    }
  }

  return (
    <div className="flex-1 overflow-y-auto p-8 pb-32">
      <div className="max-w-6xl mx-auto space-y-10">
        <section>
          <h2 className="text-heading-lg text-ink mb-2 flex items-center gap-2">
            <GitMerge className="h-5 w-5 text-accent-blue" />
            Investigation Comparison Engine
          </h2>
          <p className="text-body-sm text-mute mb-6">Select two historical investigations to perform a side-by-side actuarial comparison.</p>
          
          <div className="flex gap-3 overflow-x-auto pb-4">
            {investigations.map(inv => (
              <div 
                key={inv.id} 
                onClick={() => toggleSelection(inv.id)}
                className={`min-w-[220px] cursor-pointer p-4 rounded-[var(--radius-xl)] border transition-all ${selectedIds.includes(inv.id) ? 'border-accent-blue bg-accent-blue-soft' : 'border-hairline bg-surface hover:bg-surface-elevated'}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="text-caption-sm text-ash uppercase tracking-wider">{new Date(inv.timestamp).toLocaleDateString()}</span>
                  {selectedIds.includes(inv.id) && (
                    <CheckCircle2 className="w-4 h-4 text-accent-blue shrink-0" />
                  )}
                </div>
                <h3 className="text-body-sm-strong text-ink truncate">{inv.id}</h3>
                <p className="text-caption-sm text-mute truncate">{inv.dataset}</p>
                <div className="mt-2 inline-block px-2 py-0.5 bg-surface-elevated rounded-[var(--radius-sm)] text-caption-sm font-medium text-body border border-hairline">
                  {inv.root_cause}
                </div>
              </div>
            ))}
          </div>
        </section>

        {loading && <div className="text-mute animate-pulse text-body-sm">Loading comparison data...</div>}

        {!loading && comparisonData.length === 2 && (
          <section className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {comparisonData.map((data, idx) => (
                <div key={idx} className="space-y-4">
                  <div className="bg-surface-elevated text-ink p-5 rounded-[var(--radius-xl)] border border-hairline">
                    <h3 className="text-heading-sm text-ink mb-1">{data.investigation_id}</h3>
                    <p className="text-caption-sm text-mute">{data.dataset_metadata?.filename}</p>
                  </div>

                  <EnterpriseCard>
                    <EnterpriseCardHeader>
                      <EnterpriseCardTitle>Primary Root Cause</EnterpriseCardTitle>
                    </EnterpriseCardHeader>
                    <EnterpriseCardContent>
                      <p className="text-heading-sm text-accent-red">{data.primary_root_cause || "None Detected"}</p>
                      <p className="text-caption-sm text-mute mt-2 tabular-nums">Score: {data.explainability_report?.explainability_score || 0}/100</p>
                    </EnterpriseCardContent>
                  </EnterpriseCard>

                  <EnterpriseCard>
                    <EnterpriseCardHeader>
                      <EnterpriseCardTitle>Statistical Evidence</EnterpriseCardTitle>
                    </EnterpriseCardHeader>
                    <EnterpriseCardContent className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-body-sm text-mute">Relative Drift</span>
                        <span className="text-body-sm-strong text-ink tabular-nums">
                          {data.drift_metrics?.relative_drift !== undefined ? (data.drift_metrics.relative_drift * 100).toFixed(2) + '%' : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-body-sm text-mute">Z-Score</span>
                        <span className="text-body-sm-strong text-ink tabular-nums">
                          {data.drift_metrics?.z_score !== undefined ? data.drift_metrics.z_score.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                    </EnterpriseCardContent>
                  </EnterpriseCard>

                  <EnterpriseCard>
                    <EnterpriseCardHeader>
                      <EnterpriseCardTitle>Business Impact</EnterpriseCardTitle>
                    </EnterpriseCardHeader>
                    <EnterpriseCardContent className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-body-sm text-mute">Unexpected Claims</span>
                        <span className="text-body-sm-strong text-ink tabular-nums">+{data.business_impact?.additional_claims?.toLocaleString() || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-body-sm text-mute">Risk Level</span>
                        <span className={`text-body-sm-strong ${data.business_impact?.risk_level === 'High' ? 'text-accent-red' : 'text-accent-yellow'}`}>
                          {data.business_impact?.risk_level || 'Unknown'}
                        </span>
                      </div>
                    </EnterpriseCardContent>
                  </EnterpriseCard>

                </div>
              ))}

            </div>
          </section>
        )}
      </div>
    </div>
  )
}
