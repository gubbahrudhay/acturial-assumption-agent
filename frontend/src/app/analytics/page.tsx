"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import axios from "axios";
import { Activity, ShieldAlert, BarChart3, PieChart, Layers, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";

export default function AnalyticsDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get("http://localhost:8000/api/analytics");
        setData(res.data);
      } catch (err) {
        console.error("Error fetching analytics:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#fafafa] flex items-center justify-center">
        <p className="text-[#6a6a6a]">Loading Analytics Database...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-[#fafafa] flex items-center justify-center">
        <p className="text-[#6a6a6a]">Failed to load analytics data.</p>
      </div>
    );
  }

  const { total_investigations, total_claims_impacted, risk_breakdown, root_causes, recurring_issues } = data;

  return (
    <div className="min-h-screen bg-[#fafafa] flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="h-16 bg-white border-b border-[#ebebeb] px-6 flex items-center justify-between sticky top-0 z-30 shadow-sm">
        <div className="flex items-center gap-4">
          <Link href="/investigation" className="hover:bg-[#f0f0f0] p-2 rounded-lg transition-colors">
            <ArrowLeft className="h-5 w-5 text-[#222222]" />
          </Link>
          <h1 className="text-xl font-bold text-[#222222] flex items-center gap-2">
            <BarChart3 className="text-[#ff385c]" />
            Actuarial Intelligence Center
          </h1>
          <Badge variant="outline" className="ml-4 font-mono text-[10px] bg-[#f7f7f7]">DASHBOARD</Badge>
        </div>
      </header>

      <main className="flex-1 p-6 md:p-12 max-w-7xl mx-auto w-full">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <h2 className="text-3xl font-extrabold text-[#222222] tracking-tight mb-2">Historical Investigations</h2>
          <p className="text-[#6a6a6a]">Aggregated metrics from all prior deterministic AI investigations.</p>
        </motion.div>

        {/* Global KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <div className="bg-white p-6 rounded-2xl border border-[#dddddd] shadow-sm">
            <div className="flex items-center gap-3 mb-4 text-[#6a6a6a]">
              <Layers className="h-5 w-5" />
              <h3 className="text-sm font-bold uppercase tracking-wider">Total Investigations</h3>
            </div>
            <p className="text-4xl font-extrabold text-[#222222]">{total_investigations}</p>
          </div>
          
          <div className="bg-white p-6 rounded-2xl border border-[#dddddd] shadow-sm">
            <div className="flex items-center gap-3 mb-4 text-[#6a6a6a]">
              <Activity className="h-5 w-5" />
              <h3 className="text-sm font-bold uppercase tracking-wider">Claims Impacted</h3>
            </div>
            <p className="text-4xl font-extrabold text-[#137333]">{total_claims_impacted.toLocaleString()}</p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-[#dddddd] shadow-sm">
            <div className="flex items-center gap-3 mb-4 text-[#6a6a6a]">
              <ShieldAlert className="h-5 w-5" />
              <h3 className="text-sm font-bold uppercase tracking-wider">High Risk Events</h3>
            </div>
            <p className="text-4xl font-extrabold text-[#ff385c]">{risk_breakdown["High"]}</p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-[#dddddd] shadow-sm">
            <div className="flex items-center gap-3 mb-4 text-[#6a6a6a]">
              <PieChart className="h-5 w-5" />
              <h3 className="text-sm font-bold uppercase tracking-wider">Unique Root Causes</h3>
            </div>
            <p className="text-4xl font-extrabold text-[#fbbc04]">{root_causes.length}</p>
          </div>
        </div>

        {/* Recurring Systemic Issues Alert */}
        {recurring_issues && recurring_issues.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 bg-[#fff0f2] border border-[#ff385c] rounded-2xl p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <ShieldAlert className="h-6 w-6 text-[#ff385c]" />
              <h3 className="text-xl font-bold text-[#ff385c]">Systemic Recurring Issues Detected</h3>
            </div>
            <div className="space-y-3">
              {recurring_issues.map((issue: any, idx: number) => (
                <div key={idx} className="bg-white p-4 rounded-xl border border-[#ff385c]/30 shadow-sm flex items-center justify-between">
                  <div>
                    <p className="font-bold text-[#222222]">{issue.root_cause.replace("Root -> ", "")}</p>
                    <p className="text-sm text-[#ff385c]">{issue.warning}</p>
                  </div>
                  <Badge className="bg-[#ff385c] text-white">Occurred {issue.frequency} times</Badge>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Root Cause Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white p-8 rounded-2xl border border-[#dddddd] shadow-sm"
          >
            <h3 className="text-xl font-bold text-[#222222] mb-6">Top Isolated Root Causes</h3>
            <div className="space-y-4">
              {root_causes.length > 0 ? (
                root_causes.map((rc: any, idx: number) => {
                  const maxCount = root_causes[0].count;
                  const pct = Math.max(5, (rc.count / maxCount) * 100);
                  return (
                    <div key={idx} className="relative">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium text-[#222222] truncate max-w-[80%]">{rc.name.replace("Root -> ", "")}</span>
                        <span className="text-[#6a6a6a] font-bold">{rc.count} runs</span>
                      </div>
                      <div className="w-full bg-[#f0f0f0] rounded-full h-2">
                        <div className="bg-[#222222] h-2 rounded-full" style={{ width: `${pct}%` }}></div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="text-[#6a6a6a]">No root cause data available.</p>
              )}
            </div>
          </motion.div>

          {/* Risk Level Distribution */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white p-8 rounded-2xl border border-[#dddddd] shadow-sm"
          >
            <h3 className="text-xl font-bold text-[#222222] mb-6">Risk Profile</h3>
            <div className="space-y-6">
              {["High", "Medium", "Low"].map((level, idx) => {
                const count = risk_breakdown[level] || 0;
                const total = (risk_breakdown["High"] || 0) + (risk_breakdown["Medium"] || 0) + (risk_breakdown["Low"] || 0);
                const pct = total > 0 ? (count / total) * 100 : 0;
                let colorClass = "bg-[#137333]";
                if (level === "High") colorClass = "bg-[#ff385c]";
                if (level === "Medium") colorClass = "bg-[#fbbc04]";
                
                return (
                  <div key={idx} className="flex items-center justify-between">
                    <div className="flex items-center gap-4 w-full">
                      <div className="w-24">
                        <span className="font-bold text-[#222222]">{level} Risk</span>
                      </div>
                      <div className="flex-1 bg-[#f0f0f0] rounded-full h-3 mx-4">
                        <div className={`${colorClass} h-3 rounded-full`} style={{ width: `${pct}%` }}></div>
                      </div>
                      <div className="w-12 text-right">
                        <span className="text-[#6a6a6a] font-bold">{count}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        </div>

      </main>
    </div>
  );
}
