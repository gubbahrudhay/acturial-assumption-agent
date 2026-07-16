"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import axios from "axios";
import { Activity, ShieldAlert, BarChart3, PieChart, Layers, ArrowLeft, RefreshCw } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { API_BASE_URL } from "@/lib/api";
import { EnterpriseCard, EnterpriseCardContent, EnterpriseCardHeader, EnterpriseCardTitle } from "@/components/ui/EnterpriseCard";

export default function AnalyticsDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await axios.get(`${API_BASE_URL}/api/analytics`);
      setData(res.data);
    } catch (err) {
      setError("Failed to load analytics data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen p-6 md:p-8 lg:p-10">
        <div className="w-full max-w-7xl mx-auto">
          <div className="skeleton h-8 w-64 mb-6 rounded-[var(--radius-md)]" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            {Array.from({length: 4}).map((_, i) => <div key={i} className="skeleton h-[120px] rounded-[var(--radius-xl)]" />)}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="skeleton h-[300px] rounded-[var(--radius-xl)]" />
            <div className="skeleton h-[300px] rounded-[var(--radius-xl)]" />
          </div>
        </div>
      </div>
    );
  }

  if (!data || error) {
    return (
      <div className="flex flex-col min-h-screen p-6 md:p-8 lg:p-10">
        <div className="w-full max-w-7xl mx-auto">
          <EnterpriseCard>
            <div className="flex flex-col items-center justify-center p-16 text-center gap-3">
              <BarChart3 className="h-10 w-10 text-ash" />
              <p className="text-body-sm text-mute">{error || "No analytics data available."}</p>
              <button onClick={fetchData} className="text-accent-blue text-body-sm-strong hover:underline">Retry</button>
            </div>
          </EnterpriseCard>
        </div>
      </div>
    );
  }

  const { total_investigations, total_claims_impacted, risk_breakdown, root_causes, recurring_issues } = data;

  return (
    <div className="flex flex-col min-h-screen p-6 md:p-8 lg:p-10">
      <div className="w-full max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-10">
          <div className="flex items-center gap-4">
            <Link href="/investigation" className="hover:bg-surface-elevated p-2 rounded-[var(--radius-md)] transition-colors">
              <ArrowLeft className="h-5 w-5 text-ink" />
            </Link>
            <div>
              <motion.h1
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-display-lg text-ink tracking-tight flex items-center gap-3"
              >
                <BarChart3 className="h-8 w-8 text-accent-blue" />
                Actuarial Intelligence Center
              </motion.h1>
            </div>
          </div>
          <button onClick={fetchData} className="p-2 border border-hairline rounded-[var(--radius-md)] bg-surface text-mute hover:bg-surface-elevated hover:text-body transition-colors" aria-label="Refresh analytics">
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <EnterpriseCard>
            <EnterpriseCardContent className="p-5 flex flex-col justify-center min-h-[110px]">
              <div className="flex items-center gap-2 text-ash text-caption-sm font-medium uppercase tracking-wider mb-3">
                <Layers className="h-4 w-4" /> Total Investigations
              </div>
              <div className="text-display-sm text-ink tabular-nums">{total_investigations}</div>
            </EnterpriseCardContent>
          </EnterpriseCard>

          <EnterpriseCard>
            <EnterpriseCardContent className="p-5 flex flex-col justify-center min-h-[110px]">
              <div className="flex items-center gap-2 text-ash text-caption-sm font-medium uppercase tracking-wider mb-3">
                <Activity className="h-4 w-4" /> Claims Impacted
              </div>
              <div className="text-display-sm text-accent-green tabular-nums">{total_claims_impacted?.toLocaleString()}</div>
            </EnterpriseCardContent>
          </EnterpriseCard>

          <EnterpriseCard>
            <EnterpriseCardContent className="p-5 flex flex-col justify-center min-h-[110px]">
              <div className="flex items-center gap-2 text-ash text-caption-sm font-medium uppercase tracking-wider mb-3">
                <ShieldAlert className="h-4 w-4" /> High Risk Events
              </div>
              <div className="text-display-sm text-accent-red tabular-nums">{risk_breakdown?.["High"] ?? 0}</div>
            </EnterpriseCardContent>
          </EnterpriseCard>

          <EnterpriseCard>
            <EnterpriseCardContent className="p-5 flex flex-col justify-center min-h-[110px]">
              <div className="flex items-center gap-2 text-ash text-caption-sm font-medium uppercase tracking-wider mb-3">
                <PieChart className="h-4 w-4" /> Unique Root Causes
              </div>
              <div className="text-display-sm text-accent-yellow tabular-nums">{root_causes?.length ?? 0}</div>
            </EnterpriseCardContent>
          </EnterpriseCard>
        </div>

        {/* Recurring Issues */}
        {recurring_issues && recurring_issues.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <EnterpriseCard className="border-accent-red-soft">
              <EnterpriseCardHeader className="bg-accent-red-soft/50">
                <EnterpriseCardTitle className="flex items-center gap-2 text-accent-red">
                  <ShieldAlert className="h-5 w-5" />
                  Systemic Recurring Issues Detected
                </EnterpriseCardTitle>
              </EnterpriseCardHeader>
              <EnterpriseCardContent>
                <div className="space-y-3">
                  {recurring_issues.map((issue: any, idx: number) => (
                    <div key={idx} className="bg-surface-elevated p-4 rounded-[var(--radius-lg)] border border-hairline flex items-center justify-between gap-4">
                      <div>
                        <p className="text-body-sm-strong text-ink">{issue.root_cause?.replace("Root -> ", "")}</p>
                        <p className="text-caption-sm text-accent-red mt-0.5">{issue.warning}</p>
                      </div>
                      <Badge className="bg-accent-red text-white border-0 shrink-0">Occurred {issue.frequency} times</Badge>
                    </div>
                  ))}
                </div>
              </EnterpriseCardContent>
            </EnterpriseCard>
          </motion.div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}>
            <EnterpriseCard>
              <EnterpriseCardHeader>
                <EnterpriseCardTitle>Top Isolated Root Causes</EnterpriseCardTitle>
              </EnterpriseCardHeader>
              <EnterpriseCardContent>
                <div className="space-y-4">
                  {root_causes && root_causes.length > 0 ? (
                    root_causes.map((rc: any, idx: number) => {
                      const maxCount = root_causes[0].count;
                      const pct = Math.max(5, (rc.count / maxCount) * 100);
                      return (
                        <div key={idx}>
                          <div className="flex justify-between text-body-sm mb-1.5">
                            <span className="font-medium text-ink truncate max-w-[80%]">{rc.name?.replace("Root -> ", "")}</span>
                            <span className="text-ash font-medium tabular-nums">{rc.count} runs</span>
                          </div>
                          <div className="w-full bg-surface-elevated rounded-full h-2 border border-hairline overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${pct}%` }}
                              transition={{ duration: 0.5, delay: idx * 0.05 }}
                              className="bg-ink h-full rounded-full"
                            />
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <p className="text-mute text-body-sm">No root cause data available.</p>
                  )}
                </div>
              </EnterpriseCardContent>
            </EnterpriseCard>
          </motion.div>

          <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 }}>
            <EnterpriseCard>
              <EnterpriseCardHeader>
                <EnterpriseCardTitle>Risk Profile</EnterpriseCardTitle>
              </EnterpriseCardHeader>
              <EnterpriseCardContent>
                <div className="space-y-5">
                  {["High", "Medium", "Low"].map((level, idx) => {
                    const count = risk_breakdown?.[level] || 0;
                    const total = (risk_breakdown?.["High"] || 0) + (risk_breakdown?.["Medium"] || 0) + (risk_breakdown?.["Low"] || 0);
                    const pct = total > 0 ? (count / total) * 100 : 0;
                    const colorClass = level === "High" ? "bg-accent-red" : level === "Medium" ? "bg-accent-yellow" : "bg-accent-green";
                    
                    return (
                      <div key={idx} className="flex items-center gap-4">
                        <span className="w-20 text-body-sm-strong text-ink shrink-0">{level}</span>
                        <div className="flex-1 bg-surface-elevated rounded-full h-2.5 border border-hairline overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 0.5, delay: idx * 0.1 }}
                            className={`${colorClass} h-full rounded-full`}
                          />
                        </div>
                        <span className="w-8 text-right text-body-sm text-ash tabular-nums">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </EnterpriseCardContent>
            </EnterpriseCard>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
