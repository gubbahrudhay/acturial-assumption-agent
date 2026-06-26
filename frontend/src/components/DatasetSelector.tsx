"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { Database } from "lucide-react"
import { useStore } from "@/store/store"

export default function DatasetSelector() {
  const [datasets, setDatasets] = useState<string[]>([])
  const { dataset, setDataset } = useStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const res = await axios.get("http://localhost:8000/api/datasets")
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
      await axios.post("http://localhost:8000/api/dataset/switch", { filename })
      // We don't need a hard reload if we use global state properly, but it's okay for now.
    } catch (e) {
      console.error("Could not switch dataset", e)
    }
  }

  if (loading) return null

  return (
    <div className="flex items-center gap-2">
      <Database className="h-4 w-4 text-[#6a6a6a] hidden sm:block" />
      <select 
        value={dataset}
        onChange={handleSwitch}
        className="text-sm font-semibold text-[#222222] bg-[#f7f7f7] border border-[#dddddd] hover:bg-[#ebebeb] px-3 py-2 rounded-full transition-colors cursor-pointer outline-none focus:ring-2 focus:ring-[#ff385c]/20 max-w-[150px] sm:max-w-[200px] text-ellipsis overflow-hidden whitespace-nowrap"
      >
        {datasets.map((ds) => (
          <option key={ds} value={ds}>{ds.replace('.csv', '').replace(/_/g, ' ')}</option>
        ))}
      </select>
    </div>
  )
}
