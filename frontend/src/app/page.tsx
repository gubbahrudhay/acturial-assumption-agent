"use client"

import Link from "next/link"
import { Search, MapPin, Calendar, Users, Activity, ShieldCheck, FileText, BrainCircuit, BarChart3, TestTube, Network, ArrowRight } from "lucide-react"
import NetworkBackground from "@/components/NetworkBackground"
import { motion } from "framer-motion"

export default function LandingPage() {
  return (
    <div className="flex flex-col bg-white min-h-screen relative overflow-hidden font-sans">
      <NetworkBackground />
      
      {/* Hero Section */}
      <div className="px-6 md:px-10 pt-20 md:pt-32 max-w-[1280px] mx-auto w-full relative z-10 flex flex-col items-center text-center">
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#ff385c]/10 text-[#ff385c] font-semibold text-xs tracking-wide uppercase mb-6"
        >
          <Activity className="h-3.5 w-3.5" />
          <span>Actuarial Intelligence Platform</span>
        </motion.div>

        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
          className="text-[40px] md:text-[64px] font-extrabold text-[#222222] tracking-tight leading-[1.1] mb-6 max-w-4xl"
        >
          Monitor assumptions. <br className="hidden md:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#ff385c] to-[#e00b41]">
            Isolate root causes.
          </span>
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
          className="text-[18px] md:text-[20px] text-[#6a6a6a] max-w-2xl mb-12 leading-relaxed"
        >
          The enterprise-grade AI workspace for actuaries. Automatically detect statistical drift across your portfolio, investigate frequency and severity, and calculate the true financial impact.
        </motion.p>
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
          className="flex flex-col sm:flex-row gap-4"
        >
          <Link href="/investigation" className="px-8 py-4 rounded-full bg-[#ff385c] text-white font-bold text-[15px] hover:bg-[#e00b41] transition-all shadow-[0_8px_20px_rgba(255,56,92,0.3)] hover:shadow-[0_12px_24px_rgba(255,56,92,0.4)] flex items-center justify-center gap-2 group">
            Launch Workspace <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link href="/analytics" className="px-8 py-4 rounded-full bg-white text-[#222222] border border-[#dddddd] font-bold text-[15px] hover:bg-[#f7f7f7] transition-all flex items-center justify-center">
            Historical Analytics
          </Link>
        </motion.div>
      </div>
      
      {/* Interactive Feature Grid */}
      <div className="px-6 md:px-10 max-w-[1280px] mx-auto w-full pt-32 pb-20 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="group p-8 rounded-3xl bg-white border border-[#ebebeb] shadow-[0_4px_20px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.08)] transition-all cursor-pointer relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-[#ff385c]/5 to-transparent rounded-bl-full -z-10 group-hover:scale-110 transition-transform duration-500" />
            <div className="w-12 h-12 rounded-xl bg-[#ff385c]/10 flex items-center justify-center mb-6 text-[#ff385c]">
              <BrainCircuit className="h-6 w-6" />
            </div>
            <h3 className="text-[18px] font-bold text-[#222222] mb-3">Deterministic AI Planner</h3>
            <p className="text-[14px] text-[#6a6a6a] leading-relaxed">
              Orchestrates complex actuarial investigations using strict rule-based logic and statistical models, ensuring zero hallucination.
            </p>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="group p-8 rounded-3xl bg-white border border-[#ebebeb] shadow-[0_4px_20px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.08)] transition-all cursor-pointer relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-[#ff385c]/5 to-transparent rounded-bl-full -z-10 group-hover:scale-110 transition-transform duration-500" />
            <div className="w-12 h-12 rounded-xl bg-[#ff385c]/10 flex items-center justify-center mb-6 text-[#ff385c]">
              <Network className="h-6 w-6" />
            </div>
            <h3 className="text-[18px] font-bold text-[#222222] mb-3">Root Cause Isolation</h3>
            <p className="text-[14px] text-[#6a6a6a] leading-relaxed">
              Recursively drills down into demographic attributes to isolate the specific segments driving portfolio drift.
            </p>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="group p-8 rounded-3xl bg-white border border-[#ebebeb] shadow-[0_4px_20px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.08)] transition-all cursor-pointer relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-[#ff385c]/5 to-transparent rounded-bl-full -z-10 group-hover:scale-110 transition-transform duration-500" />
            <div className="w-12 h-12 rounded-xl bg-[#ff385c]/10 flex items-center justify-center mb-6 text-[#ff385c]">
              <TestTube className="h-6 w-6" />
            </div>
            <h3 className="text-[18px] font-bold text-[#222222] mb-3">Scenario Lab</h3>
            <p className="text-[14px] text-[#6a6a6a] leading-relaxed">
              Instantly simulate structural portfolio adjustments and what-if scenarios to recalculate financial impacts on the fly.
            </p>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="group p-8 rounded-3xl bg-white border border-[#ebebeb] shadow-[0_4px_20px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.08)] transition-all cursor-pointer relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-[#ff385c]/5 to-transparent rounded-bl-full -z-10 group-hover:scale-110 transition-transform duration-500" />
            <div className="w-12 h-12 rounded-xl bg-[#ff385c]/10 flex items-center justify-center mb-6 text-[#ff385c]">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <h3 className="text-[18px] font-bold text-[#222222] mb-3">Total Explainability</h3>
            <p className="text-[14px] text-[#6a6a6a] leading-relaxed">
              Every decision is transparent. Click into the AI's "Planner Notebook" to see the exact statistical math driving conclusions.
            </p>
          </motion.div>
          
        </div>
      </div>
      
      {/* Dual Confidence Section */}
      <div className="bg-[#f7f7f7] py-24 relative z-10 border-t border-[#ebebeb]">
        <div className="px-6 md:px-10 max-w-[1280px] mx-auto w-full grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-black/5 text-[#222222] font-semibold text-xs tracking-wide uppercase mb-6">
              <BarChart3 className="h-3.5 w-3.5" />
              <span>Unified Analytics</span>
            </div>
            <h2 className="text-[32px] md:text-[40px] font-bold text-[#222222] leading-[1.1] tracking-tight mb-6">
              Frequency and Severity. <br/> Investigated seamlessly.
            </h2>
            <p className="text-[16px] md:text-[18px] text-[#6a6a6a] leading-relaxed mb-8">
              The platform orchestrates multiple analytical engines. It independently investigates whether more claims are occurring (Frequency) and if those claims are becoming more expensive (Severity), merging the evidence into a single, comprehensive Business Impact assessment.
            </p>
            <ul className="space-y-4">
              {[
                "Calculate Expected vs Actual Financial Impact",
                "Evaluate Mathematical Materiality (Z-Scores)",
                "Identify Systemic Recurring Issues",
                "Generate Deterministic PDF Reports"
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <div className="mt-1 w-5 h-5 rounded-full bg-[#ff385c]/10 flex items-center justify-center shrink-0">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#ff385c]" />
                  </div>
                  <span className="text-[15px] text-[#222222] font-medium">{item}</span>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-tr from-[#ff385c]/20 to-transparent rounded-[2rem] transform rotate-3 blur-sm" />
            <div className="bg-white rounded-[2rem] shadow-xl border border-[#ebebeb] p-8 relative overflow-hidden">
              {/* Decorative UI elements representing the platform */}
              <div className="flex items-center justify-between border-b border-[#ebebeb] pb-4 mb-6">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-[#ff5f56]" />
                  <div className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
                  <div className="w-3 h-3 rounded-full bg-[#27c93f]" />
                </div>
                <div className="text-[11px] font-bold text-[#6a6a6a] uppercase tracking-wider">Business Impact</div>
              </div>
              
              <div className="space-y-4 mb-6">
                <div className="h-2 w-1/3 bg-[#f0f0f0] rounded-full" />
                <div className="h-8 w-2/3 bg-[#f7f7f7] rounded-lg" />
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-[#f7f7f7] p-4 rounded-xl border border-[#ebebeb]">
                  <div className="text-[12px] text-[#6a6a6a] mb-1">Expected Cost</div>
                  <div className="text-[20px] font-bold text-[#222222]">$1.24M</div>
                </div>
                <div className="bg-[#ff385c]/5 p-4 rounded-xl border border-[#ff385c]/20">
                  <div className="text-[12px] text-[#ff385c] mb-1">Observed Cost</div>
                  <div className="text-[20px] font-bold text-[#e00b41]">$1.89M</div>
                </div>
              </div>
              
              <div className="h-24 w-full bg-[#f7f7f7] rounded-xl flex items-end p-4 gap-2">
                {[40, 65, 45, 80, 55, 90, 75].map((h, i) => (
                  <motion.div 
                    key={i}
                    initial={{ height: 0 }}
                    whileInView={{ height: `${h}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: i * 0.1 }}
                    className={`flex-1 rounded-t-sm ${i === 5 ? 'bg-[#ff385c]' : 'bg-[#dddddd]'}`} 
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
      
    </div>
  )
}
