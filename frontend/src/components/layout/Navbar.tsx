import { Activity, Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface NavbarProps {
  onMenuClick: () => void;
}

export function Navbar({ onMenuClick }: NavbarProps) {
  return (
    <nav className="sticky top-0 z-40 w-full border-b border-border/80 bg-background/85 backdrop-blur-xl supports-[backdrop-filter]:bg-background/75">
      <div className="mx-auto flex h-16 max-w-[1600px] items-center gap-4 px-4 sm:px-6 lg:px-8">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={onMenuClick}
          aria-label="Toggle menu"
        >
          <Menu className="h-5 w-5" />
        </Button>

        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-gradient-to-br from-primary to-cyan-500 p-2 shadow-sm">
            <Activity className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="text-base font-semibold tracking-tight">KneeVision AI</div>
            <div className="text-[10px] uppercase tracking-[0.24em] text-muted-foreground">
              clinical intelligence
            </div>
          </div>
        </div>

        <div className="ml-auto flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 sm:flex">
            <span className="status-dot" />
            <span className="text-xs font-medium text-emerald-700">Live analysis ready</span>
          </div>
          <span className="text-sm text-muted-foreground hidden md:inline">
            AI-Powered Orthopedic Analysis
          </span>
        </div>
      </div>
    </nav>
  );
}
