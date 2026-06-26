import "./globals.css"
import Link from "next/link"
import { Activity, LayoutDashboard, SearchCode, FileText } from "lucide-react"
import DatasetSelector from "@/components/DatasetSelector"
import ApiKeyInput from "@/components/ApiKeyInput"
import UploadDatasetButton from "@/components/UploadDatasetButton"

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-white text-[#222222] antialiased selection:bg-[#ff385c]/30 font-sans">
        <div className="flex min-h-screen flex-col">
          <header className="sticky top-0 z-50 w-full h-[80px] bg-white border-b border-[#dddddd] flex items-center">
            <div className="container flex items-center justify-between px-6 md:px-10 mx-auto w-full">
              <div className="flex items-center">
                <Link href="/" className="flex items-center space-x-2 text-[#ff385c]">
                  <Activity className="h-8 w-8" />
                  <span className="hidden font-bold sm:inline-block text-xl tracking-tight">
                    assumption
                  </span>
                </Link>
              </div>
              
              {/* Center Product Tabs */}
              <nav className="hidden md:flex items-center space-x-8 text-[16px] font-semibold text-[#6a6a6a]">
                <Link href="/investigation" className="transition-colors hover:text-[#222222] flex items-center gap-2">
                  Investigation Workspace
                </Link>
              </nav>

              {/* Right Utilities */}
              <div className="flex items-center gap-4">
                 <UploadDatasetButton />
                 <DatasetSelector />
                 <ApiKeyInput />
              </div>
            </div>
          </header>
          <main className="flex-1 w-full max-w-[1280px] mx-auto">{children}</main>
        </div>
      </body>
    </html>
  )
}
