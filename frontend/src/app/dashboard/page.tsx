'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  ArrowUpRight,
  ScanLine,
  Layers,
  Target,
  FileCheck2,
  MoveUpRight,
} from 'lucide-react';
import { api } from '@/lib/api';
import type { Analysis } from '@/types';
import { PageHeading, HistoryTable, ErrorBox, EmptyState } from '@/components/ui/shared';

export default function Dashboard() {
  const [rows, setRows] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    api
      .history()
      .then(setRows)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);
  const scored = rows.filter((r) => r.match_score !== null);
  const average = scored.length
    ? Math.round(scored.reduce((a, r) => a + (r.match_score || 0), 0) / scored.length)
    : null;
  return (
    <>
      <PageHeading
        eyebrow="YOUR CAREER, WITH DIRECTION"
        title="Make your next move count."
        description="Turn your experience into a clearer path to the right opportunity."
        action={
          <Link href="/analyze" className="button black">
            New analysis <span className="button-plus">+</span>
          </Link>
        }
      />
      {error && <ErrorBox message={error} />}
      <section className="hero-card">
        <div className="hero-copy">
          <span className="eyebrow">FROM RESUME TO READY</span>
          <h2>
            Your potential.
            <br />A more precise pitch.
          </h2>
          <p>
            Five specialized AI agents connect the dots between
            <br className="desktop-break" /> your experience and your next opportunity.
          </p>
          <Link href="/analyze" className="button white">
            Analyze my resume <ArrowUpRight size={17} />
          </Link>
          <div className="hero-caption">
            <span className="tiny-dot" /> EVIDENCE FIRST. ALWAYS IN YOUR CONTROL.
          </div>
        </div>
        <div className="orbital" aria-hidden="true">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="orbit orbit-three" />
          <div className="orbit-cross horizontal" />
          <div className="orbit-cross vertical" />
          <div className="orbit-center">
            <MoveUpRight size={68} strokeWidth={0.8} />
          </div>
          <span className="orbit-label label-one">EXPERIENCE</span>
          <span className="orbit-label label-two">OPPORTUNITY</span>
          <span className="orbit-coordinate">35.0° N / NEXT</span>
        </div>
      </section>
      <section className="stat-grid">
        {[
          {
            icon: ScanLine,
            label: 'TOTAL ANALYSES',
            value: rows.length.toString().padStart(2, '0'),
            note: 'Resumes, understood',
          },
          {
            icon: Layers,
            label: 'JOBS EXPLORED',
            value: new Set(rows.map((r) => r.job_title + r.company)).size
              .toString()
              .padStart(2, '0'),
            note: 'Opportunities evaluated',
          },
          {
            icon: Target,
            label: 'AVG. COMPATIBILITY',
            value: average === null ? '—' : `${average}%`,
            note: 'Across scored analyses',
          },
          {
            icon: FileCheck2,
            label: 'REVIEWED & READY',
            value: rows
              .filter((r) => r.workflow_status.startsWith('approved'))
              .length.toString()
              .padStart(2, '0'),
            note: 'AI reviewed; confirm before sending',
          },
        ].map((stat) => (
          <div className="stat-card" key={stat.label}>
            <div className="stat-top">
              <span>{stat.label}</span>
              <stat.icon size={17} strokeWidth={1.4} />
            </div>
            <div className="stat-value">{loading ? '…' : stat.value}</div>
            <p>{stat.note}</p>
          </div>
        ))}
      </section>
      <div className="dashboard-bottom">
        <section className="panel">
          <div className="section-heading">
            <div>
              <h2>Recent opportunities</h2>
              <p>Your latest analyses, all in one place.</p>
            </div>
            <Link className="text-link" href="/history">
              View all <ArrowUpRight size={15} />
            </Link>
          </div>
          {loading ? (
            <p className="loading-copy">Loading your workspace…</p>
          ) : rows.length ? (
            <HistoryTable rows={rows.slice(0, 4)} />
          ) : (
            <EmptyState />
          )}
        </section>
        <section className="panel process-panel">
          <span className="eyebrow">A THOUGHTFUL PROCESS</span>
          <h2>
            One goal.
            <br />
            Five perspectives.
          </h2>
          {[
            ['01', 'Understand', 'Read your resume and the role.'],
            ['02', 'Connect', 'Find matches, gaps and evidence.'],
            ['03', 'Prepare', 'Draft, review and refine.'],
          ].map(([n, title, text]) => (
            <div className="process-step" key={n}>
              <span>{n}</span>
              <div>
                <strong>{title}</strong>
                <p>{text}</p>
              </div>
            </div>
          ))}
          <Link className="text-link" href="/settings">
            Inside the workflow <ArrowRight size={16} />
          </Link>
        </section>
      </div>
      <div className="privacy-strip">
        <span className="eyebrow">YOUR STORY STAYS YOURS</span>
        <p>No automatic emails. No automatic applications. You decide what happens next.</p>
        <ArrowUpRight size={17} />
      </div>
    </>
  );
}
