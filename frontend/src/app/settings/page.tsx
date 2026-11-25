'use client';
import { useEffect, useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { api } from '@/lib/api';
import type { Health } from '@/types';
import { PageHeading, ErrorBox } from '@/components/ui/shared';
export default function Settings() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <>
      <PageHeading
        eyebrow="UNDER THE HOOD"
        title="A clear view of the system."
        description="Configuration, connections, and the architecture behind every analysis."
      />
      {error && <ErrorBox message={error} />}
      <div className="two-columns">
        <section className="panel padded">
          <h2>System information</h2>
          <dl className="settings-list">
            {[
              ['Application version', health?.version],
              ['API status', health?.status],
              ['PostgreSQL', health?.database],
              ['LLM mode', health?.llm_mode],
              ['OpenAI model', health?.model],
              ['LangSmith tracing', health ? (health.tracing ? 'Enabled' : 'Disabled') : '—'],
              ['Maximum revisions', health?.max_revisions],
              ['Upload limit', health ? `${health.max_upload_mb} MB` : '—'],
            ].map(([k, v]) => (
              <div key={k}>
                <dt>{k}</dt>
                <dd>{v ?? '—'}</dd>
              </div>
            ))}
          </dl>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="text-link"
          >
            Open FastAPI API reference <ExternalLink size={14} />
          </a>
        </section>
        <section className="panel padded">
          <h2>Configuration & privacy</h2>
          <p className="body-copy">
            Configure the backend in <code>backend/.env</code> and restart FastAPI after changes.
            API keys stay on the backend.
          </p>
          <h3>Offline mock mode</h3>
          <p className="body-copy">
            Runs the actual graph with rule-based extraction, matching, templates and validation. It
            is useful for testing, but has limited language understanding.
          </p>
          <h3>Live OpenAI mode</h3>
          <p className="body-copy">
            Set LLM_MODE=live, OPENAI_API_KEY and OPENAI_MODEL. Resume text and job data are sent to
            OpenAI for structured reasoning.
          </p>
          <h3>Saved information</h3>
          <p className="body-copy">
            Extracted resume text, structured profiles and results are saved in PostgreSQL. Original
            uploaded files are not saved. Delete an analysis in history to remove its linked data.
          </p>
          <h3>LangSmith</h3>
          <p className="body-copy">
            Tracing records execution when enabled. Trace inputs and outputs are hidden by default.
            Use synthetic candidates when enabling full payload inspection.
          </p>
        </section>
      </div>
      <section className="panel padded">
        <span className="eyebrow">SYSTEM ARCHITECTURE</span>
        <h2>One backend. A coordinated workflow.</h2>
        <div className="architecture-flow">
          <span>Next.js / React</span>
          <b>→</b>
          <span>FastAPI</span>
          <b>→</b>
          <span>LangGraph</span>
          <b>→</b>
          <span>OpenAI</span>
        </div>
        <p className="body-copy">
          FastAPI also handles PostgreSQL persistence, parsing, PDF reports and REST endpoints.
          LangSmith observes execution. It does not host the application.
        </p>
      </section>
    </>
  );
}
