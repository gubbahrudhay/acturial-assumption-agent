import React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { BrainCircuit, SkipBack, Pause, Play, SkipForward, ArrowRight } from "lucide-react"

export default function PlannerNotebookTimeline({ 
  plannerNotebook, 
  isReplaying, 
  setIsReplaying, 
  replayStep, 
  setReplayStep, 
  setActiveExplainability 
}: any) {
  if (!plannerNotebook || plannerNotebook.length === 0) return null;
  const displaySteps = isReplaying ? plannerNotebook.slice(0, replayStep) : plannerNotebook;
  
  return (
    <div className="mb-12">
      <div className="flex items-center justify-between mb-8 border-b border-hairline pb-4">
        <h2 className="text-heading-lg text-ink flex items-center gap-2">
          <BrainCircuit className="h-6 w-6 text-accent-blue" />
          AI Execution Trace
        </h2>
        <div className="flex items-center gap-2 bg-surface-elevated border border-hairline rounded-[var(--radius-lg)] px-2 py-1">
          <button onClick={() => {setIsReplaying(true); setReplayStep(Math.max(1, replayStep - 1))}} className="p-1.5 hover:bg-surface text-mute hover:text-body rounded-[var(--radius-md)] transition-colors"><SkipBack className="h-4 w-4" /></button>
          {isReplaying ? (
             <button onClick={() => setIsReplaying(false)} className="p-1.5 hover:bg-surface text-mute hover:text-body rounded-[var(--radius-md)] transition-colors"><Pause className="h-4 w-4" /></button>
          ) : (
             <button onClick={() => {setIsReplaying(true); if(replayStep === plannerNotebook.length) setReplayStep(1); }} className="p-1.5 hover:bg-surface text-mute hover:text-body rounded-[var(--radius-md)] transition-colors"><Play className="h-4 w-4" /></button>
          )}
          <button onClick={() => {setIsReplaying(true); setReplayStep(Math.min(plannerNotebook.length, replayStep + 1))}} className="p-1.5 hover:bg-surface text-mute hover:text-body rounded-[var(--radius-md)] transition-colors"><SkipForward className="h-4 w-4" /></button>
        </div>
      </div>
      
      <div className="space-y-6">
        <AnimatePresence>
          {displaySteps.map((entry: any, i: number) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
              className="flex"
            >
              <div className="flex flex-col items-center mr-6">
                <div className="w-8 h-8 rounded-full bg-accent-blue-soft border border-hairline flex items-center justify-center text-caption-sm font-bold text-accent-blue z-10 shadow-sm">
                  {i+1}
                </div>
                {i < displaySteps.length - 1 && <div className="w-px h-full bg-hairline mt-2" />}
              </div>
              <div className="flex-1 bg-surface border border-hairline rounded-[var(--radius-lg)] p-5 shadow-sm hover:shadow-md hover:border-hairline-strong transition-all cursor-pointer group"
                   onClick={() => setActiveExplainability({type: 'planner_step', step: entry})}>
                <div className="grid grid-cols-1 gap-3 text-body-sm">
                  <div className="flex"><span className="w-24 shrink-0 font-semibold text-ash uppercase tracking-wider text-[11px] pt-0.5">Observation</span> <span className="text-ink font-medium">{entry.observation}</span></div>
                  <div className="flex"><span className="w-24 shrink-0 font-semibold text-ash uppercase tracking-wider text-[11px] pt-0.5">Hypothesis</span> <span className="text-body">{entry.hypothesis}</span></div>
                  <div className="flex"><span className="w-24 shrink-0 font-semibold text-accent-blue uppercase tracking-wider text-[11px] pt-0.5">Decision</span> <span className="text-ink font-semibold flex items-center gap-1"><ArrowRight className="w-3 h-3 text-accent-blue" /> {entry.decision}</span></div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
