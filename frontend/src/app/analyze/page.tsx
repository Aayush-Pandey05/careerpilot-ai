'use client';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Upload, FileText, X, Download } from 'lucide-react';
import { api, analyzeStream } from '@/lib/api';
import { PageHeading, ErrorBox } from '@/components/ui/shared';
import AgentMonitor from '@/components/analysis/agent-monitor';
import type { AgentEvent, Health } from '@/types';

const sampleJob = `Title: AI/ML Intern\nCompany: Northstar Labs\nRequired skills:\nPython, SQL, pandas, scikit-learn, Git\nPreferred skills:\nDocker, AWS, TensorFlow\nResponsibilities:\nBuild and evaluate machine learning models.\nEducation:\nA degree in computer science or a related field.`;
export default function Analyze() {
  const router = useRouter();
  const controller = useRef<AbortController | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [jd, setJd] = useState('');
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('');
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [health, setHealth] = useState<Health | null>(null);
  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch(() => {});
    return () => controller.current?.abort();
  }, []);
  function selectFile(value: File | undefined) {
    if (!value) return;
    if (!/\.(pdf|docx)$/i.test(value.name)) {
      setError('Choose a PDF or DOCX resume.');
      return;
    }
    if (value.size > (health?.max_upload_mb || 10) * 1024 * 1024) {
      setError('The resume exceeds the upload size limit.');
      return;
    }
    setError('');
    setFile(value);
  }
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setError('Choose your resume first.');
      return;
    }
    setBusy(true);
    setError('');
    setEvents([]);
    controller.current = new AbortController();
    const form = new FormData();
    form.append('resume', file);
    form.append('job_description', jd);
    form.append('job_title', title);
    form.append('company', company);
    try {
      await analyzeStream(
        form,
        (event) => {
          setEvents((old) => [...old, event]);
          if (event.analysis) router.push(`/results/${event.analysis.id}`);
        },
        controller.current.signal,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed.');
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="A BETTER APPLICATION STARTS HERE"
        title="Find where you fit."
        description="Bring your experience. We’ll help you connect it to the opportunity."
      />
      {error && <ErrorBox message={error} />}
      <div className="analysis-layout">
        <form className="analysis-form" onSubmit={submit}>
          <section className="panel form-section">
            <div className="section-heading">
              <div>
                <span className="eyebrow">01 / YOUR EXPERIENCE</span>
                <h2>Start with your resume</h2>
              </div>
              <span className="pill">PDF OR DOCX</span>
            </div>
            <input
              ref={input}
              type="file"
              accept=".pdf,.docx"
              className="sr-only"
              aria-label="Upload resume"
              disabled={busy}
              onChange={(e) => selectFile(e.target.files?.[0])}
            />
            <button
              type="button"
              disabled={busy}
              className="upload-zone"
              onClick={() => input.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                if (!busy) selectFile(e.dataTransfer.files[0]);
              }}
            >
              <Upload size={28} strokeWidth={1.1} />
              <strong>Drop your resume here, or browse files</strong>
              <span>Text-based PDF or DOCX · Up to {health?.max_upload_mb || 10} MB</span>
            </button>
            {file && (
              <div className="selected-file">
                <FileText size={18} />
                <span>
                  {file.name}
                  <small>{Math.ceil(file.size / 1024)} KB</small>
                </span>
                <button
                  type="button"
                  className="icon-button"
                  disabled={busy}
                  aria-label="Remove resume"
                  onClick={() => setFile(null)}
                >
                  <X size={16} />
                </button>
              </div>
            )}
            <div className="form-footnote">
              Original files are processed in memory. Extracted text is saved for review and
              regeneration.
            </div>
          </section>
          <section className="panel form-section">
            <div className="section-heading">
              <div>
                <span className="eyebrow">02 / THE OPPORTUNITY</span>
                <h2>Tell us about the role</h2>
              </div>
              <button
                type="button"
                className="text-link"
                disabled={busy}
                onClick={() => setJd(sampleJob)}
              >
                Use sample role <ArrowRight size={14} />
              </button>
            </div>
            <div className="field-grid">
              <label>
                Job title <span className="muted">(optional)</span>
                <input
                  value={title}
                  maxLength={250}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. AI/ML Intern"
                  disabled={busy}
                />
              </label>
              <label>
                Company <span className="muted">(optional)</span>
                <input
                  value={company}
                  maxLength={250}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="e.g. Northstar Labs"
                  disabled={busy}
                />
              </label>
            </div>
            <label>
              Job description
              <textarea
                required
                minLength={40}
                maxLength={40000}
                value={jd}
                onChange={(e) => setJd(e.target.value)}
                rows={11}
                placeholder="Paste the full job description, including required skills, responsibilities and preferred qualifications…"
                disabled={busy}
              />
            </label>
            <div className="field-count">{jd.length.toLocaleString()} / 40,000 characters</div>
          </section>
          <div className="submit-row">
            <p>
              {health?.llm_mode === 'live'
                ? 'Resume and job data will be sent to OpenAI.'
                : 'Offline mock mode uses deterministic extraction and templates. No OpenAI calls.'}
            </p>
            <button className="button black" disabled={busy || !file || jd.trim().length < 40}>
              {busy ? 'Agents at work…' : 'Run analysis'}
              <ArrowRight size={17} />
            </button>
          </div>
        </form>
        <aside className="analysis-aside">
          <section className="panel">
            <div className="section-heading">
              <div>
                <span className="eyebrow">THE WORKFLOW</span>
                <h2>Your team of agents</h2>
              </div>
              <span className="pill">{busy ? 'RUNNING' : 'READY'}</span>
            </div>
            <AgentMonitor events={events} running={busy} />
          </section>
          <section className="demo-note">
            <span className="eyebrow">PREPARING FOR A DEMO?</span>
            <h3>Try a synthetic resume.</h3>
            <p>
              Use our sample candidate and sample role to explore the complete workflow without
              personal data.
            </p>
            <a href="/sample_resume.pdf" download className="text-link">
              <Download size={15} /> Download sample PDF
            </a>
            <a href="/sample_resume.docx" download className="text-link">
              <Download size={15} /> Download sample DOCX
            </a>
          </section>
        </aside>
      </div>
    </>
  );
}
