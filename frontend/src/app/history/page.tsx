'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowUpRight, Trash2, Search, Plus } from 'lucide-react';
import { api } from '@/lib/api';
import type { Analysis } from '@/types';
import { PageHeading, EmptyState, ErrorBox, StatusPill } from '@/components/ui/shared';
const statuses = [
  'Analyzed',
  'Ready to Apply',
  'Applied',
  'Interview Scheduled',
  'Rejected',
  'Selected',
];
export default function History() {
  const [rows, setRows] = useState<Analysis[]>([]);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState('');
  useEffect(() => {
    api
      .history()
      .then(setRows)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);
  async function remove(id: string) {
    if (!confirm('Delete this analysis, its extracted resume data and application permanently?'))
      return;
    setPending(id);
    try {
      await api.remove(id);
      setRows((old) => old.filter((r) => r.id !== id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPending('');
    }
  }
  async function update(row: Analysis, status: string) {
    setPending(row.id);
    try {
      await api.status(row.application_id, status);
      setRows((old) =>
        old.map((r) => (r.id === row.id ? { ...r, application_status: status } : r)),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPending('');
    }
  }
  const visible = rows.filter((r) =>
    `${r.job_title} ${r.company}`.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <>
      <PageHeading
        eyebrow="EVERY OPPORTUNITY, IN PERSPECTIVE"
        title="Your application journal."
        description="Revisit your results, compare opportunities, and keep track of your next steps."
        action={
          <Link className="button black" href="/analyze">
            New analysis <Plus size={17} />
          </Link>
        }
      />
      {error && <ErrorBox message={error} />}
      <section className="panel">
        <div className="section-heading">
          <h2>
            All opportunities <span className="count-badge">{rows.length}</span>
          </h2>
          <label className="search-field">
            <Search size={16} />
            <input
              aria-label="Search opportunities"
              placeholder="Search role or company"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
        </div>
        {loading ? (
          <p className="loading-copy">Loading your history…</p>
        ) : visible.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>OPPORTUNITY</th>
                  <th>COMPATIBILITY</th>
                  <th>REVIEW</th>
                  <th>APPLICATION STATUS</th>
                  <th>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <Link className="role-link" href={`/results/${row.id}`}>
                        {row.job_title}
                      </Link>
                      <span className="table-sub">
                        {row.company || 'Company not specified'} ·{' '}
                        {new Date(row.created_at).toLocaleDateString('en-IN')}
                      </span>
                    </td>
                    <td>
                      <span className="table-score">
                        {row.match_score ?? '—'}
                        <small>/100</small>
                      </span>
                    </td>
                    <td>
                      <StatusPill value={row.workflow_status} />
                    </td>
                    <td>
                      <select
                        aria-label={`Status for ${row.job_title}`}
                        value={row.application_status}
                        disabled={pending === row.id}
                        onChange={(e) => update(row, e.target.value)}
                      >
                        {statuses.map((s) => (
                          <option key={s}>{s}</option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <div className="inline-actions">
                        <Link
                          className="icon-button"
                          aria-label="Open analysis"
                          href={`/results/${row.id}`}
                        >
                          <ArrowUpRight size={17} />
                        </Link>
                        <button
                          className="icon-button"
                          disabled={pending === row.id}
                          aria-label={`Delete ${row.job_title}`}
                          onClick={() => remove(row.id)}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : query ? (
          <p className="loading-copy">No opportunities match your search.</p>
        ) : (
          <EmptyState />
        )}
      </section>
      <p className="page-note">
        Application status is updated by you. It does not reflect automatic employer tracking.
        History shows the latest 200 analyses.
      </p>
    </>
  );
}
