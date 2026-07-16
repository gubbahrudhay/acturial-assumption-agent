import React from "react"
import Link from "next/link"
import { Database, Activity, FileText, SearchCode, PlayCircle } from "lucide-react"

const ActionButton = ({ href, icon: Icon, title, description, colorClass }: any) => (
  <Link href={href} className="group flex flex-col items-center justify-center p-6 bg-surface border border-hairline rounded-[var(--radius-lg)] hover:bg-surface-elevated hover:border-hairline-strong transition-all duration-200 text-center">
    <div className={`p-3 rounded-full mb-3 transition-colors ${colorClass}`}>
      <Icon className="w-5 h-5" />
    </div>
    <span className="text-body-sm-strong text-ink group-hover:text-white transition-colors">{title}</span>
    <span className="text-caption-sm text-mute mt-1 px-2">{description}</span>
  </Link>
)

export default function QuickActions() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
      <ActionButton href="/" icon={Database} title="Upload Dataset" description="Process new experience data" colorClass="bg-accent-blue-soft text-accent-blue" />
      <ActionButton href="/data-readiness" icon={SearchCode} title="Data Readiness" description="Run quality schemas" colorClass="bg-white/10 text-white" />
      <ActionButton href="/investigation" icon={Activity} title="Run Investigation" description="Launch AI root cause analysis" colorClass="bg-accent-red-soft text-accent-red" />
      <ActionButton href="/history" icon={PlayCircle} title="Replay Run" description="Audit past planner traces" colorClass="bg-accent-yellow-soft text-accent-yellow" />
      <ActionButton href="/reports" icon={FileText} title="View Reports" description="Access executive PDFs" colorClass="bg-accent-green-soft text-accent-green" />
    </div>
  )
}
