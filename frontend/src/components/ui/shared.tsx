'use client';
import Link from 'next/link';
import { ArrowUpRight, ArrowRight, AlertCircle, FileSearch } from 'lucide-react';
import type { Analysis } from '@/types';

export function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}
export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="error-box" role="alert">
      <AlertCircle size={18} />
      <span>{message}</span>
    </div>
  );
}
export function EmptyState({
  title = 'Your next chapter starts here.',
  text = 'Upload a resume and a job description to create your first evidence-based analysis.',
}: {
  title?: string;
  text?: string;
}) {
  return (
    <div className="empty-state">
      <FileSearch size={32} strokeWidth={1} />
      <h3>{title}</h3>
      <p>{text}</p>
      <Link className="button black" href="/analyze">
        Start an analysis <ArrowRight size={16} />
      </Link>
    </div>
  );
}
export function StatusPill({ value }: { value: string }) {
  return (
    <span
      className={`pill ${value.includes('failed') || value.includes('manual') ? 'warning' : ''}`}
    >
      {value.replaceAll('_', ' ')}
    </span>
  );
}
export function HistoryTable({ rows }: { rows: Analysis[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>OPPORTUNITY</th>
            <th>DATE</th>
            <th>COMPATIBILITY</th>
            <th>REVIEW STATUS</th>
            <th>
              <span className="sr-only">Open</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>
                <Link className="role-link" href={`/results/${row.id}`}>
                  {row.job_title}
                </Link>
                <span className="table-sub">{row.company || 'Company not specified'}</span>
              </td>
              <td className="muted">
                {new Date(row.created_at).toLocaleDateString('en-IN', {
                  day: '2-digit',
                  month: 'short',
                  year: 'numeric',
                })}
              </td>
              <td>
                <span className="table-score">
                  {row.match_score ?? '—'}
                  <small>{row.match_score !== null ? '/100' : ''}</small>
                </span>
                <div className="mini-track">
                  <span style={{ width: `${row.match_score || 0}%` }} />
                </div>
              </td>
              <td>
                <StatusPill value={row.workflow_status} />
              </td>
              <td>
                <Link
                  className="icon-button"
                  aria-label={`Open ${row.job_title}`}
                  href={`/results/${row.id}`}
                >
                  <ArrowUpRight size={18} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function BulletList({ items }: { items: string[] }) {
  return items.length ? (
    <ul className="detail-list">
      {items.map((s, i) => (
        <li key={i}>{s}</li>
      ))}
    </ul>
  ) : (
    <p className="muted">No information available.</p>
  );
}
