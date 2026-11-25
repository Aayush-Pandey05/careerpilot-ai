'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  ArrowUpRight,
  LayoutDashboard,
  ScanLine,
  History,
  Settings,
  Compass,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Health } from '@/types';

const links = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/analyze', label: 'New analysis', icon: ScanLine },
  { href: '/history', label: 'Application history', icon: History },
  { href: '/settings', label: 'System & settings', icon: Settings },
];
export default function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [health, setHealth] = useState<Health | null>(null);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, [path]);
  return (
    <div className="app-frame">
      <button
        className="mobile-menu icon-button"
        aria-label="Toggle navigation"
        onClick={() => setOpen(!open)}
      >
        {open ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
      </button>
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <Link className="brand" href="/dashboard">
          <span className="brand-mark">
            <Compass size={23} strokeWidth={1.4} />
          </span>
          <span>
            careerpilot<span className="brand-ai">AI</span>
          </span>
        </Link>
        <div className="workspace-tag">
          <span className="tiny-dot" /> PERSONAL WORKSPACE
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav>
          {links.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className={`nav-item ${path.startsWith(item.href) ? 'active' : ''}`}
            >
              <item.icon size={18} strokeWidth={1.5} />
              {item.label}
              {item.href === '/analyze' && <span className="nav-plus">+</span>}
            </Link>
          ))}
        </nav>
        <div className="sidebar-note">
          <span className="eyebrow">BUILT AROUND YOUR NEXT STEP</span>
          <p>
            A little clarity.
            <br />A better application.
          </p>
          <Link href="/analyze">
            Find your fit <ArrowUpRight size={16} />
          </Link>
        </div>
        <div className="sidebar-bottom">
          <div className="avatar">CP</div>
          <div>
            <strong>CareerPilot workspace</strong>
            <span>
              {health
                ? `${health.llm_mode === 'mock' ? 'Offline mock' : 'Live OpenAI'} mode`
                : 'Backend disconnected'}
            </span>
          </div>
          <span className="tiny-dot" />
        </div>
      </aside>
      <div className="main-frame">
        <header className="topbar">
          <span>
            WORKSPACE <span className="muted">/</span>{' '}
            {path.startsWith('/results')
              ? 'ANALYSIS RESULTS'
              : links.find((l) => path.startsWith(l.href))?.label.toUpperCase() || 'OVERVIEW'}
          </span>
          <div className="topbar-right">
            <span className="status-dot" />
            {health
              ? health.llm_mode === 'mock'
                ? 'OFFLINE MOCK MODE'
                : 'LIVE OPENAI MODE'
              : 'API DISCONNECTED'}
            <span className="top-avatar">CP</span>
          </div>
        </header>
        <main>{children}</main>
        <footer>
          CAREERPILOT AI <span>Thoughtful applications start with evidence.</span>
          <span>v1.0 / {new Date().getFullYear()}</span>
        </footer>
      </div>
    </div>
  );
}
