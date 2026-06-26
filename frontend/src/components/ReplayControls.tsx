import React, { useEffect } from 'react'
import { Play, Pause, SkipBack, SkipForward, RotateCcw } from 'lucide-react'
import { Button } from "@/components/ui/button"

interface ReplayControlsProps {
  isReplaying: boolean;
  setIsReplaying: (val: boolean) => void;
  replayStep: number;
  setReplayStep: (val: number | ((prev: number) => number)) => void;
  maxSteps: number;
}

export default function ReplayControls({ 
  isReplaying, setIsReplaying, replayStep, setReplayStep, maxSteps 
}: ReplayControlsProps) {

  // Auto-play logic
  useEffect(() => {
    let interval: any;
    if (isReplaying) {
      interval = setInterval(() => {
        setReplayStep((prev) => {
          if (prev >= maxSteps) {
            setIsReplaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1500); // 1.5s per step
    }
    return () => clearInterval(interval);
  }, [isReplaying, maxSteps, setReplayStep, setIsReplaying]);

  if (maxSteps === 0) return null;

  const progress = maxSteps > 0 ? (replayStep / maxSteps) * 100 : 0;

  return (
    <div className="bg-[#1a1a1a] border border-[#333333] p-4 rounded-xl shadow-xl flex flex-col gap-3 mb-8">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="icon" 
            className="text-[#aaaaaa] hover:text-white"
            onClick={() => { setIsReplaying(false); setReplayStep(0); }}
            disabled={replayStep === 0 && !isReplaying}
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            className="text-[#aaaaaa] hover:text-white"
            onClick={() => { setIsReplaying(false); setReplayStep(Math.max(0, replayStep - 1)); }}
            disabled={replayStep === 0}
          >
            <SkipBack className="h-4 w-4" />
          </Button>
          
          <Button 
            variant="default" 
            size="icon" 
            className="bg-[#222222] hover:bg-[#333333] text-white border border-[#444444] rounded-full h-10 w-10"
            onClick={() => setIsReplaying(!isReplaying)}
          >
            {isReplaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5 ml-1" />}
          </Button>

          <Button 
            variant="ghost" 
            size="icon" 
            className="text-[#aaaaaa] hover:text-white"
            onClick={() => { setIsReplaying(false); setReplayStep(Math.min(maxSteps, replayStep + 1)); }}
            disabled={replayStep >= maxSteps}
          >
            <SkipForward className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="text-[#aaaaaa] font-mono text-sm font-bold">
          Step {replayStep} / {maxSteps}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-2 w-full bg-[#222222] rounded-full overflow-hidden">
        <div 
          className="h-full bg-emerald-400 transition-all duration-300 ease-linear" 
          style={{ width: `${progress}%` }} 
        />
      </div>
      <p className="text-[10px] uppercase font-bold text-[#6a6a6a] tracking-wider text-center">
        Investigation Replay Engine
      </p>
    </div>
  )
}
