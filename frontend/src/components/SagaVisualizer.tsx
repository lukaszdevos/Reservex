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
      <div className="flex gap-2">
        {steps.map((step, i) => (
          <div key={step.name} className="flex items-center gap-2 flex-1">
            <div
              className={`
                flex-1 flex flex-col items-center py-3 px-2 rounded-md border text-xs font-mono
                ${STATUS_STYLES[step.status]}
              `}
            >
              <span className="text-lg mb-1">{STEP_ICONS[step.name] ?? '?'}</span>
              <span className="font-semibold">{step.name}</span>
              <span className="text-[10px] mt-0.5 opacity-70">{step.status}</span>
            </div>
            {i < steps.length - 1 && (
              <span className="text-text-dim text-xs">&rarr;</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
