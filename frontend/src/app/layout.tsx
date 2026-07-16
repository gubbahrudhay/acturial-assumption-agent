import "./globals.css"
import { Inter } from 'next/font/google';
import Sidebar from "@/components/Sidebar"
import TopBar from "@/components/TopBar"

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' })

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`bg-canvas text-body antialiased font-sans ${inter.variable} min-h-screen flex selection:bg-accent-blue-soft selection:text-accent-blue`}>
        {/* Sidebar Navigation */}
        <Sidebar />
        
        {/* Main Content Area */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Top Utilities Bar */}
          <TopBar />
          
          {/* Page Content */}
          <main className="flex-1 overflow-y-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
