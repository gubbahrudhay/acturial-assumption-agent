"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import axios from "axios"
import { API_BASE_URL } from "@/lib/api"
import { useStore } from "@/store/store"

import ExecutiveSummaryCard from "@/components/dashboard/ExecutiveSummaryCard"
import PortfolioKPIRow from "@/components/dashboard/PortfolioKPIRow"
import PortfolioHealthTimeline from "@/components/dashboard/PortfolioHealthTimeline"
import QuickActions from "@/components/dashboard/QuickActions"

export default function ExecutiveDashboard() {
  const dataset = useStore((state) => state.dataset)
  const [analytics, setAnalytics] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/api/analytics`)
        setAnalytics(res.data)
      } catch (err) {
        console.error("Failed to load analytics", err)
      } finally {
        setLoading(false)
      }
    }
    fetchAnalytics()
  }, [])

  return (
    <div className="flex flex-col min-h-screen p-6 md:p-8 lg:p-12">
      <div className="w-full max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-12">
          <div>
            <motion.h1 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-display-lg text-ink"
            >
              Dashboard
            </motion.h1>
            <motion.p 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-body-lg text-mute mt-2"
            >
              Portfolio health, drift detection, and automated insights
            </motion.p>
          </div>
        </div>

        <div className="flex flex-col gap-6 w-full">
          {/* KPI Row */}
          <PortfolioKPIRow />

          <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
            {/* Main Health Summary */}
            <div className="xl:col-span-8 flex flex-col gap-6">
              <ExecutiveSummaryCard analytics={analytics} dataset={dataset} />
              <QuickActions />
            </div>

            {/* Timeline Sidebar */}
            <div className="xl:col-span-4">
              <PortfolioHealthTimeline />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
