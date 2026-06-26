import Link from "next/link"
import { Search, MapPin, Calendar, Users, Activity, ShieldCheck, FileText } from "lucide-react"
import NetworkBackground from "@/components/NetworkBackground"

export default function LandingPage() {
  return (
    <div className="flex flex-col bg-white pb-20 relative">
      <NetworkBackground />
      
      {/* Hero Section */}
      <div className="px-6 md:px-10 pt-10 md:pt-16 max-w-[1280px] mx-auto w-full relative z-10">
        <h1 className="text-[28px] md:text-[32px] font-bold text-[#222222] tracking-tight mb-8">
          Inspiration for future assumptions
        </h1>
        
        {/* Global Search Bar Pill */}
        <div className="flex flex-col md:flex-row items-center border border-[#dddddd] rounded-full shadow-[0_4px_12px_rgba(0,0,0,0.05)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] transition-shadow bg-white/90 backdrop-blur-md h-auto md:h-16 w-full max-w-4xl mb-16 overflow-hidden">
          
          <div className="flex-1 px-8 py-3 w-full hover:bg-[#f7f7f7] rounded-full cursor-pointer transition-colors border-b md:border-b-0 md:border-r border-[#dddddd]">
            <div className="text-[12px] font-bold text-[#222222] tracking-wide uppercase">Dataset</div>
            <div className="text-[14px] text-[#6a6a6a]">Select experience data</div>
          </div>
          
          <div className="flex-1 px-8 py-3 w-full hover:bg-[#f7f7f7] rounded-full cursor-pointer transition-colors border-b md:border-b-0 md:border-r border-[#dddddd]">
            <div className="text-[12px] font-bold text-[#222222] tracking-wide uppercase">Metric</div>
            <div className="text-[14px] text-[#6a6a6a]">Claim Frequency</div>
          </div>
          
          <div className="flex-1 px-8 py-3 w-full hover:bg-[#f7f7f7] rounded-full cursor-pointer transition-colors flex items-center justify-between">
            <div>
              <div className="text-[12px] font-bold text-[#222222] tracking-wide uppercase">Action</div>
              <div className="text-[14px] text-[#6a6a6a]">Detect Drift</div>
            </div>
            
            <Link href="/investigation" className="h-12 w-12 rounded-full bg-[#ff385c] hover:bg-[#e00b41] flex items-center justify-center text-white transition-colors flex-shrink-0">
              <Search className="h-5 w-5" />
            </Link>
          </div>
          
        </div>
      </div>
      
      {/* Category Strip / Highlights */}
      <div className="px-6 md:px-10 max-w-[1280px] mx-auto w-full grid grid-cols-1 sm:grid-cols-3 gap-6 mb-16">
        
        <div className="group cursor-pointer">
          <div className="aspect-[4/3] rounded-2xl bg-[#f7f7f7] flex items-center justify-center mb-3 overflow-hidden">
            <Activity className="h-16 w-16 text-[#dddddd] group-hover:scale-110 transition-transform duration-500" />
          </div>
          <h3 className="text-[16px] font-semibold text-[#222222]">Drift Detection</h3>
          <p className="text-[14px] text-[#6a6a6a]">Statistically identify when actual claim frequencies deviate.</p>
        </div>
        
        <div className="group cursor-pointer">
          <div className="aspect-[4/3] rounded-2xl bg-[#f7f7f7] flex items-center justify-center mb-3 overflow-hidden relative">
            <div className="absolute top-3 left-3 bg-white px-2 py-1 rounded-full text-[11px] font-semibold text-[#222222] shadow-sm">AI Agent</div>
            <ShieldCheck className="h-16 w-16 text-[#dddddd] group-hover:scale-110 transition-transform duration-500" />
          </div>
          <h3 className="text-[16px] font-semibold text-[#222222]">Recursive Investigation</h3>
          <p className="text-[14px] text-[#6a6a6a]">The AI autonomously isolates the exact portfolio segments.</p>
        </div>
        
        <div className="group cursor-pointer">
          <div className="aspect-[4/3] rounded-2xl bg-[#f7f7f7] flex items-center justify-center mb-3 overflow-hidden">
            <FileText className="h-16 w-16 text-[#dddddd] group-hover:scale-110 transition-transform duration-500" />
          </div>
          <h3 className="text-[16px] font-semibold text-[#222222]">Actionable Reports</h3>
          <p className="text-[14px] text-[#6a6a6a]">Generate clear, explainable actuarial recommendations.</p>
        </div>
        
      </div>
      
      {/* About Project Section */}
      <div className="bg-[#f7f7f7] py-16 md:py-24 mt-10">
        <div className="px-6 md:px-10 max-w-[1280px] mx-auto w-full grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-[28px] font-bold text-[#222222] mb-6">About this project</h2>
            <p className="text-[16px] text-[#6a6a6a] leading-relaxed mb-6">
              The <strong>Assumption Monitoring Agent</strong> is a state-of-the-art AI application designed to autonomously monitor, investigate, and report on actuarial claim frequencies. Instead of relying on manual slicing and dicing of data in spreadsheets, this system acts as a virtual actuarial analyst.
            </p>
            <p className="text-[16px] text-[#6a6a6a] leading-relaxed mb-6">
              Powered by <strong>Google Gemini</strong> and a sophisticated <strong>LangGraph</strong> multi-agent architecture, the system orchestrates specialized sub-agents:
            </p>
            <ul className="space-y-3 text-[15px] text-[#222222] font-medium">
              <li className="flex items-center gap-3"><div className="w-1.5 h-1.5 rounded-full bg-[#ff385c]" /> The Planner Agent orchestrates the workflow.</li>
              <li className="flex items-center gap-3"><div className="w-1.5 h-1.5 rounded-full bg-[#ff385c]" /> The Investigation Agent recursively isolates sub-segment drift.</li>
              <li className="flex items-center gap-3"><div className="w-1.5 h-1.5 rounded-full bg-[#ff385c]" /> The Report Agent synthesizes the findings into human-readable recommendations.</li>
            </ul>
            <div className="mt-10">
              <Link href="/dashboard" className="text-[15px] font-bold border-b-2 border-[#222222] pb-1 hover:text-[#6a6a6a] hover:border-[#6a6a6a] transition-colors">
                View Live Dashboard
              </Link>
            </div>
          </div>
          <div className="bg-white rounded-2xl shadow-sm border border-[#dddddd] p-8 md:p-12">
            <h3 className="text-[20px] font-bold text-[#222222] mb-6 border-b border-[#dddddd] pb-4">Architecture Highlights</h3>
            <div className="space-y-6">
              <div>
                <h4 className="text-[14px] font-bold text-[#222222] uppercase tracking-wide">Frontend</h4>
                <p className="text-[15px] text-[#6a6a6a] mt-1">Built with Next.js App Router, React, and Tailwind CSS. Features dynamic routing and a sleek, premium minimalist UI.</p>
              </div>
              <div>
                <h4 className="text-[14px] font-bold text-[#222222] uppercase tracking-wide">Backend</h4>
                <p className="text-[15px] text-[#6a6a6a] mt-1">High-performance FastAPI server running in Python, serving data and orchestrating AI chains.</p>
              </div>
              <div>
                <h4 className="text-[14px] font-bold text-[#222222] uppercase tracking-wide">Intelligence</h4>
                <p className="text-[15px] text-[#6a6a6a] mt-1">LangChain and LangGraph power a state-driven multi-agent framework, interpreting statistical variance through Gemini 1.5.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  )
}
