import React from "react"
import { EnterpriseCard, EnterpriseCardHeader, EnterpriseCardTitle, EnterpriseCardContent } from "@/components/ui/EnterpriseCard"

export default function InvestigationMetricsTabs({ businessImpact, activeTab, setActiveTab }: any) {
  const tabs = [
    { key: "frequency", label: "Frequency Engine" },
    { key: "severity", label: "Severity Engine" },
    { key: "combined", label: "Combined Cost Engine" },
  ]

  return (
    <section>
      <h2 className="text-heading-lg text-ink mb-6">Business Impact & Analytics</h2>
      
      {/* Tab Selector */}
      <div className="flex border-b border-hairline mb-6 gap-1">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`py-2.5 px-5 text-body-sm font-medium border-b-2 transition-all rounded-t-[var(--radius-sm)] ${
              activeTab === tab.key
                ? "border-accent-blue text-accent-blue bg-accent-blue-soft"
                : "border-transparent text-mute hover:text-body hover:bg-surface"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <EnterpriseCard className="md:col-span-1">
          <EnterpriseCardHeader>
            <EnterpriseCardTitle className="text-caption-sm uppercase tracking-wider">
              {activeTab === "frequency" && "Frequency Metrics"}
              {activeTab === "severity" && "Severity Metrics"}
              {activeTab === "combined" && "Combined Cost Metrics"}
            </EnterpriseCardTitle>
          </EnterpriseCardHeader>
          <EnterpriseCardContent>
            {activeTab === "frequency" && (
              <>
                <div className="flex items-end gap-2 mb-1">
                  <p className="text-display-sm text-accent-red tabular-nums">
                    {businessImpact?.observed_frequency !== undefined ? (businessImpact.observed_frequency * 100).toFixed(2) + '%' : 'N/A'}
                  </p>
                </div>
                <p className="text-body-sm text-mute">Expected: {businessImpact?.expected_frequency !== undefined ? (businessImpact.expected_frequency * 100).toFixed(2) + '%' : 'N/A'}</p>
                <div className="mt-5 pt-5 border-t border-hairline">
                   <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-1">Unexpected Claims</p>
                   <p className="text-heading-lg text-ink tabular-nums">+{businessImpact?.additional_claims?.toLocaleString() || 0}</p>
                </div>
                <div className="mt-4">
                   <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-1">Affected Exposure</p>
                   <p className="text-heading-lg text-ink tabular-nums">{businessImpact?.affected_policies_percentage !== undefined ? (businessImpact.affected_policies_percentage * 100).toFixed(1) + '%' : 'N/A'}</p>
                </div>
              </>
            )}
            {activeTab === "severity" && (
              <>
                <div className="flex items-end gap-2 mb-1">
                  <p className="text-display-sm text-accent-red tabular-nums">
                    {businessImpact?.observed_severity?.toLocaleString(undefined, {maximumFractionDigits: 0}) || 
                     (businessImpact?.observed_claim_cost && businessImpact?.claim_count ? (businessImpact.observed_claim_cost / businessImpact.claim_count).toLocaleString(undefined, {maximumFractionDigits: 0}) : 'N/A')}
                  </p>
                </div>
                <p className="text-body-sm text-mute">Expected: {businessImpact?.expected_severity?.toLocaleString(undefined, {maximumFractionDigits: 0}) || 'N/A'}</p>
                <div className="mt-5 pt-5 border-t border-hairline">
                   <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-1">Excess Claim Cost</p>
                   <p className="text-heading-lg text-ink tabular-nums">
                     +{businessImpact?.excess_cost?.toLocaleString(undefined, {maximumFractionDigits: 0}) || 0}
                   </p>
                </div>
                <div className="mt-4">
                   <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-1">Claims Affected</p>
                   <p className="text-heading-lg text-ink tabular-nums">{businessImpact?.claim_count?.toLocaleString() || 0}</p>
                </div>
              </>
            )}
            {activeTab === "combined" && (
              <>
                <div className="flex flex-col gap-1 mb-1">
                  <p className="text-caption-sm text-ash uppercase tracking-wider font-medium">Primary Pattern</p>
                  <p className="text-body-sm-strong text-accent-red">{businessImpact?.deterioration_pattern || 'No Material Combined Deterioration'}</p>
                </div>
                <div className="mt-5 pt-5 border-t border-hairline">
                  <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-1">Observed Claim Cost</p>
                  <p className="text-heading-lg text-ink tabular-nums">₹{businessImpact?.observed_claim_cost?.toLocaleString(undefined, {maximumFractionDigits: 0}) || 0}</p>
                </div>
                <div className="mt-4">
                  <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-1">Expected Claim Cost</p>
                  <p className="text-heading-lg text-mute tabular-nums">₹{businessImpact?.expected_claim_cost?.toLocaleString(undefined, {maximumFractionDigits: 0}) || 0}</p>
                </div>
                <div className="mt-4">
                  <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-1">Combined Cost O/E</p>
                  <p className="text-heading-lg text-ink tabular-nums">
                    {businessImpact?.expected_claim_cost ? (businessImpact.observed_claim_cost / businessImpact.expected_claim_cost).toFixed(2) : '1.00'}
                  </p>
                </div>
                <div className="mt-4">
                  <p className="text-caption-sm text-ash uppercase tracking-wider font-medium mb-1">Excess Claim Cost</p>
                  <p className="text-heading-lg text-accent-red tabular-nums">₹{businessImpact?.excess_claim_cost?.toLocaleString(undefined, {maximumFractionDigits: 0}) || 0}</p>
                </div>
              </>
            )}
          </EnterpriseCardContent>
        </EnterpriseCard>

        {/* Chart space */}
        <EnterpriseCard className="md:col-span-2 flex items-center justify-center min-h-[300px]">
           <p className="text-mute text-body-sm">Chart Visualization Coming Soon</p>
        </EnterpriseCard>
      </div>
    </section>
  )
}
