import BoardroomChat from './components/BoardroomChat'

export default function App() {
  return (
    <div className="h-screen flex flex-col overflow-hidden bg-brand-white">
      {/* Navigation header */}
      <header className="bg-brand-navy flex-shrink-0">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img
              src="/logo-icon.png"
              alt="Excelerate"
              className="h-8 w-auto"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
            <div>
              <p className="text-white font-extrabold text-xs uppercase tracking-[0.2em] leading-none">Excelerate</p>
              <p className="text-brand-blue/70 text-[10px] font-semibold uppercase tracking-wider leading-none mt-0.5">C-Suite Boardroom</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-brand-blue animate-pulse" />
            <span className="text-white/40 text-xs font-medium uppercase tracking-wider">5 Agents Ready</span>
          </div>
        </div>
      </header>

      {/* Subheader — visible only on empty state */}
      <div className="bg-brand-navy/5 border-b border-brand-navy/10 flex-shrink-0 px-6 py-3">
        <div className="max-w-3xl mx-auto">
          <p className="text-brand-navy/50 text-xs leading-relaxed">
            Bring any business decision to the boardroom. Your CEO, CFO, COO, CMO, and CTO will deliberate in real time and deliver a consensus recommendation.
          </p>
        </div>
      </div>

      {/* Main content — fills remaining height */}
      <main className="flex-1 overflow-hidden">
        <BoardroomChat />
      </main>
    </div>
  )
}
