import type { SagaStepStatus } from '../types'
import { useStore } from '../store/useStore'

const STEP_META: Record<string, { icon: string; label: string; detail: string }> = {
  validate:  { icon: '✔', label: 'Validate', detail: 'Check user + ticket availability' },
  reserve:   { icon: '🎫', label: 'Reserve', detail: 'Lock seat, create reservation (5 min TTL)' },
  charge:    { icon: '💳', label: 'Charge', detail: 'Stripe gateway - Semaphore(10) guarded' },
  notify:    { icon: '📧', label: 'Notify', detail: 'SMTP via ThreadPoolExecutor' },
}

const STATUS_STYLES: Record<SagaStepStatus, string> = {
  pending: 'border-border bg-surface-alt text-text-dim',
  running: 'border-accent bg-accent/10 text-accent-light animate-pulse-glow',
  success: 'border-success bg-success/10 text-success',
  failed:  'border-error bg-error/10 text-error',
}

const STATUS_LABEL_COLORS: Record<SagaStepStatus, string> = {
  pending: 'text-text-dim/50',
  running: 'text-accent-light',
  success: 'text-success',
  failed:  'text-error',
}

export function SagaVisualizer() {
  const steps = useStore((s) => s.sagaSteps)
  const runningScenario = useStore((s) => s.runningScenario)
  const lastScenario = useStore((s) => s.lastScenario)
  const hasSagaProgress = steps.some((step) => step.status !== 'pending')
  const isSagaActive =
    runningScenario === 'saga' || (lastScenario === 'saga' && hasSagaProgress)

  return (
    <div className={`bg-surface rounded-lg border p-4 transition-all duration-300 ${
      isSagaActive ? 'border-accent/60 shadow-[0_0_16px_rgba(124,58,237,0.15)]' : 'border-border'
    }`}>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider">
          SAGA Steps
        </h2>
        {runningScenario === 'saga' && (
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-accent/20 text-accent-light animate-pulse-glow">
            orchestrating
          </span>
        )}
      </div>

      {/* Step flow */}
      <div className="flex gap-1.5 overflow-x-auto pb-1 hide-scrollbar">
        {steps.map((step, i) => {
          const meta = STEP_META[step.name] ?? { icon: '?', label: step.name, detail: '' }
          return (
            <div key={step.name} className="flex items-center gap-1 flex-shrink-0">
              <div
                className={`
                  w-[68px] flex flex-col items-center py-2 px-1 rounded-md border text-xs font-mono
                  transition-all duration-300
                  ${STATUS_STYLES[step.status]}
                `}
                title={meta.detail}
              >
                <span className="text-base mb-0.5">{meta.icon}</span>
                <span className="font-semibold text-[10px] leading-tight text-center">{meta.label}</span>
                <span className={`text-[9px] mt-0.5 font-mono leading-none capitalize ${STATUS_LABEL_COLORS[step.status]}`}>
                  {step.status}
                </span>
              </div>
              {i < steps.length - 1 && (
                <span className={`text-xs flex-shrink-0 transition-colors duration-300 ${
                  steps[i].status === 'success' ? 'text-success' : 'text-border'
                }`}>→</span>
              )}
            </div>
          )
        })}
      </div>

      {/* Compensation indicator */}
      {steps.some(s => s.status === 'failed') && (
        <div className="mt-2 flex items-center gap-1.5 text-[10px] font-mono text-error animate-fade-in">
          <span>↩</span>
          <span>Compensating in reverse order…</span>
        </div>
      )}

      {/* All success indicator */}
      {steps.every(s => s.status === 'success') && (
        <div className="mt-2 flex items-center gap-1.5 text-[10px] font-mono text-success animate-fade-in">
          <span>✓</span>
          <span>All steps committed - ticket confirmed</span>
        </div>
      )}
    </div>
  )
}
