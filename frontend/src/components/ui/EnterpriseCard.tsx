import React from "react";
import { cn } from "@/lib/utils";

interface EnterpriseCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  elevated?: boolean;
}

export function EnterpriseCard({ children, className, elevated = false, ...props }: EnterpriseCardProps) {
  return (
    <div
      className={cn(
        "rounded-[var(--radius-xl)] border border-hairline transition-all duration-200 overflow-hidden",
        "hover:border-hairline-strong",
        elevated ? "bg-surface-elevated" : "bg-surface",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function EnterpriseCardHeader({ children, className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("px-6 py-5 border-b border-hairline flex flex-col space-y-1.5", className)} {...props}>
      {children}
    </div>
  );
}

export function EnterpriseCardTitle({ children, className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn("font-medium text-heading-sm text-ink", className)} {...props}>
      {children}
    </h3>
  );
}

export function EnterpriseCardDescription({ children, className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-body-sm text-mute", className)} {...props}>
      {children}
    </p>
  );
}

export function EnterpriseCardContent({ children, className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-6", className)} {...props}>
      {children}
    </div>
  );
}

export function EnterpriseCardFooter({ children, className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("flex items-center px-6 py-4 border-t border-hairline", className)} {...props}>
      {children}
    </div>
  );
}
