import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { ArrowRight, GitMerge, FileText, AlertTriangle } from 'lucide-react'

export default function ComparisonWorkspace() {
  const [investigations, setInvestigations] = useState<any[]>([])
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [comparisonData, setComparisonData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  // Fetch list of investigations
  useEffect(() => {
    const fetchList = async () => {
      try {
        const res = await axios.get("http://localhost:8000/api/investigations")
        setInvestigations(res.data.investigations || [])
      } catch (e) {
        console.error("Failed to fetch investigations", e)
      }
    }
    fetchList()
  }, [])

  // Fetch full data for selected investigations
  useEffect(() => {
    const fetchComparison = async () => {
      if (selectedIds.length !== 2) {
        setComparisonData([])
        return
      }
      setLoading(true)
      try {
        const res1 = await axios.get(`http://localhost:8000/api/investigation/${selectedIds[0]}`)
        const res2 = await axios.get(`http://localhost:8000/api/investigation/${selectedIds[1]}`)
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
    <div className="flex-1 overflow-y-auto bg-[#fcfcfc] p-8 pb-32">
      <div className="max-w-6xl mx-auto space-y-12">
        <section>
          <h2 className="text-2xl font-bold text-[#222222] mb-6 flex items-center gap-2">
            <GitMerge className="h-6 w-6 text-[#ff385c]" />
            Investigation Comparison Engine
          </h2>
          <p className="text-[#6a6a6a] mb-6">Select two historical investigations to perform a side-by-side actuarial comparison.</p>
          
          <div className="flex gap-4 overflow-x-auto pb-4">
            {investigations.map(inv => (
              <div 
                key={inv.id} 
                onClick={() => toggleSelection(inv.id)}
                className={`min-w-[250px] cursor-pointer p-4 rounded-xl border ${selectedIds.includes(inv.id) ? 'border-[#ff385c] bg-[#fff5f6]' : 'border-[#dddddd] bg-white'} shadow-sm transition-all`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[10px] uppercase font-bold text-[#aaaaaa]">{new Date(inv.timestamp).toLocaleDateString()}</span>
                  {selectedIds.includes(inv.id) && <span className="w-4 h-4 rounded-full bg-[#ff385c] flex items-center justify-center text-white text-[10px]">✓</span>}
                </div>
                <h3 className="font-bold text-[#222222] truncate">{inv.id}</h3>
                <p className="text-sm text-[#6a6a6a] truncate">{inv.dataset}</p>
                <div className="mt-3 inline-block px-2 py-1 bg-[#f0f0f0] rounded-md text-xs font-bold text-[#222222]">
                  {inv.root_cause}
                </div>
              </div>
            ))}
          </div>
        </section>

        {loading && <div className="text-[#6a6a6a] animate-pulse">Loading comparison data...</div>}

        {!loading && comparisonData.length === 2 && (
          <section className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              
              {comparisonData.map((data, idx) => (
                <div key={idx} className="space-y-6">
                  <div className="bg-[#222222] text-white p-6 rounded-2xl shadow-lg">
                    <h3 className="font-bold text-xl mb-1">{data.investigation_id}</h3>
                    <p className="text-[#aaaaaa] text-sm">{data.dataset_metadata?.filename}</p>
                  </div>

                  <Card className="bg-white border-[#dddddd] shadow-sm">
                    <CardHeader className="pb-2 border-b border-[#ebebeb]">
                      <CardTitle className="text-sm text-[#222222] font-bold">Primary Root Cause</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4">
                      <p className="text-lg font-bold text-[#ff385c]">{data.primary_root_cause || "None Detected"}</p>
                      <p className="text-sm text-[#6a6a6a] mt-2">Score: {data.explainability_report?.explainability_score || 0}/100</p>
                    </CardContent>
                  </Card>

                  <Card className="bg-white border-[#dddddd] shadow-sm">
                    <CardHeader className="pb-2 border-b border-[#ebebeb]">
                      <CardTitle className="text-sm text-[#222222] font-bold">Statistical Evidence</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4 space-y-4">
                      <div className="flex justify-between">
                        <span className="text-sm text-[#6a6a6a]">Relative Drift</span>
                        <span className="font-bold text-[#222222]">
                          {data.drift_metrics?.relative_drift !== undefined ? (data.drift_metrics.relative_drift * 100).toFixed(2) + '%' : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-[#6a6a6a]">Z-Score</span>
                        <span className="font-bold text-[#222222]">
                          {data.drift_metrics?.z_score !== undefined ? data.drift_metrics.z_score.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-white border-[#dddddd] shadow-sm">
                    <CardHeader className="pb-2 border-b border-[#ebebeb]">
                      <CardTitle className="text-sm text-[#222222] font-bold">Business Impact</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4 space-y-4">
                      <div className="flex justify-between">
                        <span className="text-sm text-[#6a6a6a]">Unexpected Claims</span>
                        <span className="font-bold text-[#222222]">+{data.business_impact?.additional_claims?.toLocaleString() || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-[#6a6a6a]">Risk Level</span>
                        <span className={`font-bold ${data.business_impact?.risk_level === 'High' ? 'text-[#ff385c]' : 'text-[#fbbc04]'}`}>
                          {data.business_impact?.risk_level || 'Unknown'}
                        </span>
                      </div>
                    </CardContent>
                  </Card>

                </div>
              ))}

            </div>
          </section>
        )}
      </div>
    </div>
  )
}
