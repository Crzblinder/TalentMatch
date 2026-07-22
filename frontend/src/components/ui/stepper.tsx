import * as React from 'react'
import { Check } from 'lucide-react'

import { cn } from '@/lib/utils'

// 单个步骤的数据结构
export interface StepperStep {
  label: string
  description?: string
}

// Stepper 组件属性
interface StepperProps extends React.HTMLAttributes<HTMLDivElement> {
  steps: StepperStep[]
  currentStep: number
  orientation?: 'horizontal' | 'vertical'
}

const Stepper = React.forwardRef<HTMLDivElement, StepperProps>(
  ({ steps, currentStep, orientation = 'horizontal', className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'flex',
          orientation === 'horizontal'
            ? 'flex-row items-center justify-between'
            : 'flex-col gap-1',
          className
        )}
        {...props}
      >
        {steps.map((step, index) => {
          const stepNumber = index + 1
          const isCompleted = currentStep > stepNumber
          const isCurrent = currentStep === stepNumber

          return (
            <React.Fragment key={index}>
              <div
                className={cn(
                  'flex items-center',
                  orientation === 'vertical'
                    ? 'gap-3'
                    : 'flex flex-1 flex-col items-center gap-2'
                )}
              >
                {/* 步骤圆圈：已完成显示对勾，当前高亮，未开始置灰 */}
                <div
                  className={cn(
                    'flex h-8 w-8 items-center justify-center rounded-full border-2 text-sm font-semibold transition-colors',
                    isCompleted
                      ? 'border-primary bg-primary text-primary-foreground'
                      : isCurrent
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-muted-foreground/30 text-muted-foreground'
                  )}
                >
                  {isCompleted ? <Check className="h-4 w-4" /> : stepNumber}
                </div>
                {/* 步骤标题与描述 */}
                <div className={cn(orientation === 'vertical' ? 'flex flex-col' : 'text-center')}>
                  <span
                    className={cn(
                      'text-sm font-medium',
                      isCurrent ? 'text-foreground' : 'text-muted-foreground'
                    )}
                  >
                    {step.label}
                  </span>
                  {step.description && (
                    <span className="text-xs text-muted-foreground">{step.description}</span>
                  )}
                </div>
              </div>
              {/* 水平步骤之间的连接线 */}
              {index < steps.length - 1 && orientation === 'horizontal' && (
                <div
                  className={cn(
                    'mx-2 h-0.5 flex-1 transition-colors',
                    currentStep > stepNumber ? 'bg-primary' : 'bg-muted'
                  )}
                />
              )}
            </React.Fragment>
          )
        })}
      </div>
    )
  }
)
Stepper.displayName = 'Stepper'

export { Stepper }
