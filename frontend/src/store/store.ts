import { create } from 'zustand'

export interface AgentState {
  dataset: string
  drift: any
  investigationTree: any
  businessImpact: any
  plannerNotebook: any[]
  eventReconstruction: string
  decisionOptions: any[]
  scenario: any
  copilotMessages: any[]
  report: string
  primaryRootCause: string
  explainabilityReport: any
  isLoading: boolean
  setDataset: (dataset: string) => void
  setLoading: (isLoading: boolean) => void
  setAgentData: (data: any) => void
  setBusinessImpact: (impact: any) => void
  addCopilotMessage: (msg: any) => void
}

export const useStore = create<AgentState>((set) => ({
  dataset: 'insurance_experience.csv',
  drift: null,
  investigationTree: null,
  businessImpact: null,
  plannerNotebook: [],
  eventReconstruction: '',
  decisionOptions: [],
  scenario: {},
  copilotMessages: [],
  report: '',
  primaryRootCause: '',
  explainabilityReport: null,
  isLoading: false,

  setDataset: (dataset: string) => set({ dataset }),
  setLoading: (isLoading: boolean) => set({ isLoading }),
  
  setAgentData: (data: any) => set({
    drift: data.drift_metrics,
    investigationTree: data.tree,
    businessImpact: data.business_impact,
    decisionOptions: data.decision_options,
    plannerNotebook: data.planner_notebook || [],
    eventReconstruction: data.event_reconstruction || "",
    copilotMessages: data.chat_history || [],
    report: data.report,
    primaryRootCause: data.primary_root_cause || '',
    explainabilityReport: data.explainability_report || null
  }),
  
  setBusinessImpact: (impact: any) => set({ businessImpact: impact }),
  addCopilotMessage: (msg: any) => set((state) => ({ 
    copilotMessages: [...state.copilotMessages, msg] 
  }))
}))
