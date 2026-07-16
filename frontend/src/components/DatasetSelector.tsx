"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { Database, Loader2, Check } from "lucide-react"
import { API_BASE_URL } from "@/lib/api"
import { useStore } from "@/store/store"

export default function DatasetSelector() {
  const [datasets, setDatasets] = useState<string[]>([])
  const { dataset, setDataset } = useStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/api/datasets`)
        setDatasets(res.data.datasets)
        setDataset(res.data.active)
      } catch (e) {
        console.error("Could not load datasets", e)
      } finally {
        setLoading(false)
      }
    }
    fetchDatasets()
  }, [])

  const handleSwitch = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const filename = e.target.value
    setDataset(filename)
    try {
      await axios.post(`${API_BASE_URL}/api/dataset/switch`, { filename })
      window.location.reload()
    } catch (e) {
      console.error("Could not switch dataset", e)
    }
  }

  if (loading) return null

  return (
    <div className="flex items-center gap-2">
      <Database className="h-4 w-4 text-mute hidden sm:block" />
      <select 
        value={dataset}
        onChange={handleSwitch}
        className="text-body-sm-strong text-ink bg-surface border border-hairline hover:bg-surface-elevated px-3 py-1.5 rounded-[var(--radius-md)] transition-colors cursor-pointer outline-none focus:ring-2 focus:ring-white/20 max-w-[150px] sm:max-w-[200px] text-ellipsis overflow-hidden whitespace-nowrap appearance-none"
      >
        {datasets.map((ds) => (
          <option key={ds} value={ds}>{ds.replace('.csv', '').replace(/_/g, ' ')}</option>
        ))}
      </select>
    </div>
  )
}
