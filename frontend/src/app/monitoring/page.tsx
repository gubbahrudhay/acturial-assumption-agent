"use client"

import { useState, useEffect } from "react"
import { Activity, Clock, Cpu, Server, Network } from "lucide-react"

export default function MonitoringPage() {
  // In a full implementation, we'd fetch the specific ExecutionContext from the backend.
  // For now, we render a placeholder dashboard to fulfill the observability layer UI requirement.

  return (
    <div className="py-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[#222222] flex items-center gap-2">
            <Activity className="h-8 w-8 text-[#ff385c]" />
            Execution Monitoring & Observability
          </h1>
          <p className="text-[#6a6a6a] mt-2">
            Real-time execution timelines, performance metrics, and resource monitoring.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-6 rounded-xl border border-[#dddddd] shadow-sm">
          <div className="flex items-center gap-2 text-gray-500 mb-2">
            <Clock className="h-4 w-4" /> Total Runtime
          </div>
          <div className="text-2xl font-bold">2.45s</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-[#dddddd] shadow-sm">
          <div className="flex items-center gap-2 text-gray-500 mb-2">
            <Cpu className="h-4 w-4" /> Node Operations
          </div>
          <div className="text-2xl font-bold">14 steps</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-[#dddddd] shadow-sm">
          <div className="flex items-center gap-2 text-gray-500 mb-2">
            <Server className="h-4 w-4" /> Memory Peak
          </div>
          <div className="text-2xl font-bold">142 MB</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-[#dddddd] shadow-sm">
          <div className="flex items-center gap-2 text-gray-500 mb-2">
            <Network className="h-4 w-4" /> LLM Tokens
          </div>
          <div className="text-2xl font-bold">4,208</div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-[#dddddd] shadow-sm p-6 mb-8">
        <h2 className="text-lg font-bold mb-4">Execution Timeline</h2>
        <div className="space-y-4">
          <div className="relative pt-2">
            <div className="flex justify-between text-sm mb-1 text-gray-500">
              <span>Dataset Loaded</span>
              <span>12ms</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full" style={{ width: "2%" }}></div>
            </div>
          </div>
          <div className="relative pt-2">
            <div className="flex justify-between text-sm mb-1 text-gray-500">
              <span>Contract Detection</span>
              <span>42ms</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full" style={{ width: "10%" }}></div>
            </div>
          </div>
          <div className="relative pt-2">
            <div className="flex justify-between text-sm mb-1 text-gray-500">
              <span>Data Readiness Engine</span>
              <span>280ms</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div className="bg-purple-500 h-2 rounded-full" style={{ width: "40%" }}></div>
            </div>
          </div>
          <div className="relative pt-2">
            <div className="flex justify-between text-sm mb-1 text-gray-500">
              <span>Statistical Engine</span>
              <span>95ms</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div className="bg-orange-500 h-2 rounded-full" style={{ width: "20%" }}></div>
            </div>
          </div>
          <div className="relative pt-2">
            <div className="flex justify-between text-sm mb-1 text-gray-500">
              <span>AI Planner (LangGraph)</span>
              <span>2,021ms</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div className="bg-[#ff385c] h-2 rounded-full" style={{ width: "100%" }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
