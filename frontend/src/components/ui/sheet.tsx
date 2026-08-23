import * as React from "react"
import { cn } from "@/lib/utils"

interface SheetContextValue {
  open: boolean
  setOpen: (open: boolean) => void
}

const SheetContext = React.createContext<SheetContextValue | undefined>(undefined)

function Sheet({ children, open, onOpenChange }: { children: React.ReactNode; open?: boolean; onOpenChange?: (open: boolean) => void }) {
  const [internalOpen, setInternalOpen] = React.useState(false)
  
  const isControlled = open !== undefined
  const isOpen = isControlled ? open : internalOpen
  const setOpen = React.useCallback((newOpen: boolean) => {
    if (!isControlled) {
      setInternalOpen(newOpen)
    }
    onOpenChange?.(newOpen)
  }, [isControlled, onOpenChange])

  return (
    <SheetContext.Provider value={{ open: isOpen, setOpen }}>
      {children}
    </SheetContext.Provider>
  )
}

function SheetTrigger({ children, asChild }: { children: React.ReactNode; asChild?: boolean }) {
  const context = React.useContext(SheetContext)
  if (!context) throw new Error('SheetTrigger must be used within Sheet')

  const child = React.Children.only(children) as React.ReactElement
  
  if (asChild) {
    return React.cloneElement(child, {
      onClick: () => context.setOpen(true)
    })
  }

  return (
    <button onClick={() => context.setOpen(true)}>
      {children}
    </button>
  )
}

function SheetContent({ children, className, side = 'left' }: { children: React.ReactNode; className?: string; side?: 'left' | 'right' }) {
  const context = React.useContext(SheetContext)
  if (!context) throw new Error('SheetContent must be used within Sheet')

  if (!context.open) return null

  const sideStyles = {
    left: 'inset-y-0 left-0 h-full w-3/4 sm:max-w-sm',
    right: 'inset-y-0 right-0 h-full w-3/4 sm:max-w-sm',
  }

  return (
    <>
      <div
        className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
        onClick={() => context.setOpen(false)}
      />
      <div
        className={cn(
          "fixed z-50 gap-4 bg-background p-6 shadow-lg transition ease-in-out",
          sideStyles[side],
          className
        )}
      >
        {children}
      </div>
    </>
  )
}

function SheetHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex flex-col space-y-2 text-center sm:text-left", className)}>
      {children}
    </div>
  )
}

function SheetTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <h2 className={cn("text-lg font-semibold text-foreground", className)}>
      {children}
    </h2>
  )
}

export { Sheet, SheetTrigger, SheetContent, SheetHeader, SheetTitle }
