"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Activity, LayoutDashboard, Database, SearchCode, History, FileText, ActivitySquare } from "lucide-react"

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Readiness', href: '/data-readiness', icon: Database },
  { name: 'Investigation', href: '/investigation', icon: SearchCode },
  { name: 'History', href: '/history', icon: History },
  { name: 'Reports', href: '/reports', icon: FileText },
  { name: 'Monitoring', href: '/monitoring', icon: ActivitySquare },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex h-full w-[220px] flex-col border-r border-hairline bg-canvas shrink-0">
      {/* Brand */}
      <div className="flex h-16 shrink-0 items-center px-5 border-b border-hairline">
        <Link href="/" className="flex items-center gap-2.5 text-ink hover:text-white transition-colors">
          <Activity className="h-5 w-5 text-accent-blue" />
          <span className="text-heading-sm font-semibold tracking-tight">Agentic Pricing</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col overflow-y-auto px-3 py-4" role="navigation" aria-label="Main navigation">
        <ul className="space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href || (pathname.startsWith(`${item.href}/`) && item.href !== '/')
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  aria-current={isActive ? 'page' : undefined}
                  className={`
                    group relative flex items-center gap-3 px-3 py-2 text-body-sm rounded-[var(--radius-md)] transition-all duration-150
                    ${isActive 
                      ? 'bg-surface-elevated text-ink font-medium' 
                      : 'text-mute hover:bg-surface hover:text-body'
                    }
                  `}
                >
                  {/* Active indicator bar */}
                  {isActive && (
                    <span className="absolute -left-3 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-full bg-accent-blue" />
                  )}
                  <item.icon
                    className={`
                      h-4 w-4 shrink-0 transition-colors duration-150
                      ${isActive ? 'text-accent-blue' : 'text-ash group-hover:text-mute'}
                    `}
                    aria-hidden="true"
                  />
                  {item.name}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* System status footer */}
      <div className="px-3 py-3 border-t border-hairline">
        <div className="flex items-center gap-2 px-3 py-2 rounded-[var(--radius-md)] bg-surface">
          <span className="h-2 w-2 rounded-full bg-accent-green animate-pulse" />
          <span className="text-caption-sm text-mute">System Online</span>
        </div>
      </div>
    </div>
  )
}
