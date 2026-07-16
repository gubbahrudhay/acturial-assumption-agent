import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-transparent bg-clip-padding text-button-md whitespace-nowrap transition-all outline-none select-none focus-visible:ring-2 focus-visible:ring-white/20 active:translate-y-px disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-primary text-on-primary hover:bg-primary-pressed active:bg-primary-pressed",
        secondary:
          "bg-transparent text-on-dark hover:bg-white/10 active:bg-white/20",
        tertiary:
          "bg-surface-elevated text-on-dark hover:bg-white/10 active:bg-white/20",
        ghost:
          "hover:bg-white/10 hover:text-on-dark text-mute",
        destructive:
          "bg-accent-red-soft text-accent-red hover:bg-accent-red hover:text-white",
        link: "text-on-dark underline-offset-4 hover:underline",
      },
      size: {
        default: "h-[36px] px-4 py-2 gap-2 [&_svg:not([class*='size-'])]:size-4",
        sm: "h-[28px] px-3 py-1 gap-1.5 text-caption-md [&_svg:not([class*='size-'])]:size-3.5",
        lg: "h-[44px] px-6 py-3 gap-2.5 text-body-md [&_svg:not([class*='size-'])]:size-5",
        icon: "size-[36px]",
        "icon-sm": "size-[28px]",
        "icon-lg": "size-[44px]",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariants>) {
  return (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
