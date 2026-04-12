import type { SagaStepStatus } from '../types'
import { useStore } from '../store/useStore'

const STEP_ICONS: Record<string, string> = {
  validate: '\u2714',
  reserve: '\uD83C\uDFAB',
  charge: '\uD83D\uDCB3',
  notify: '\uD83D\uDCE7',
}

const STATUS_STYLES: Record<SagaStepStatus, string> = {
  pending: 'border-border bg-surface-alt text-text-dim',
  running: 'border-accent bg-accent/10 text-accent-light animate-pulse-glow',
  success: 'border-success bg-success/10 text-success',
  failed: 'border-error bg-error/10 text-error',
}

export function SagaVisualizer() {
  const steps = useStore((s) => s.sagaSteps)

  return (
    <div className="bg-surface rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider mb-3">
        SAGA Steps
      </h2>
      <div className="flex gap-2 overflow-x-auto pb-2 snap-x hide-scrollbar">
        {steps.map((step, i) => (
          <div key={step.name} className="flex items-center gap-2 flex-shrink-0 snap-start">
            <div
              className={`
                w-16 flex-none flex flex-col items-center py-2 px-1 rounded-md border text-xs font-mono
                ${STATUS_STYLES[step.status]}
              `}
            >
              <span className="text-lg mb-0.5">{STEP_ICONS[step.name] ?? '?'}</span>
              <span className="font-semibold text-[10px] leading-tight text-center">{step.name}</span>
              <span className="text-[9px] mt-0.5 opacity-70 leading-none">{step.status}</span>
            </div>
            {i < steps.length - 1 && (
              <span className="text-text-dim text-xs flex-shrink-0">&rarr;</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
