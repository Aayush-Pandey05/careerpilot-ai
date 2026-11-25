'use client';
import { use, useEffect, useState } from 'react';
import { Copy, Download, RefreshCw, Save, Check, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { api, downloadText } from '@/lib/api';
import type { Analysis, Materials } from '@/types';
import { PageHeading, ErrorBox, StatusPill, BulletList } from '@/components/ui/shared';
import AgentMonitor from '@/components/analysis/agent-monitor';
import InterviewCoach from '@/features/interview/coach';

const sectionNames = {
  subject: 'Email subject',
  email: 'Application email',
  cover_letter: 'Cover letter',
  professional_summary: 'Professional summary',
  resume_suggestions: 'Resume improvement suggestions',
  keywords: 'Suggested keywords',
  project_suggestions: 'Project presentation suggestions',
  interview_questions: 'Interview preparation questions',
};
type Section = keyof typeof sectionNames;
function sectionText(materials: Materials, section: Section) {
  const value = materials[section];
  return Array.isArray(value) ? value.join('\n') : value;
}
function Editor({
  row,
  section,
  onUpdate,
}: {
  row: Analysis;
  section: Section;
  onUpdate: (row: Analysis) => void;
}) {
  const [content, setContent] = useState(sectionText(row.result.application as Materials, section));
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  useEffect(() => {
    setContent(sectionText(row.result.application as Materials, section));
  }, [row, section]);
  async function action(kind: 'save' | 'regenerate') {
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const result =
        kind === 'save'
          ? await api.edit(row.id, section, content)
          : await api.regenerate(row.id, section);
      onUpdate(result);
      setMessage(kind === 'save' ? 'Saved and reviewed.' : 'Section regenerated and reviewed.');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel editor-panel">
      <div className="section-heading">
        <h2>{sectionNames[section]}</h2>
        <div className="inline-actions">
          <button
            className="icon-button"
            aria-label={`Copy ${sectionNames[section]}`}
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(content);
                setMessage('Copied.');
              } catch {
                setError('Clipboard unavailable. Select the text and copy manually.');
              }
            }}
          >
            <Copy size={16} />
          </button>
          <button
            className="icon-button"
            aria-label={`Download ${sectionNames[section]}`}
            onClick={() => downloadText(content, `careerpilot-${section}.txt`)}
          >
            <Download size={16} />
          </button>
        </div>
      </div>
      <textarea
        aria-label={sectionNames[section]}
        value={content}
        onChange={(e) => {
          setContent(e.target.value);
          setMessage('Unsaved changes');
        }}
        maxLength={20000}
        rows={section === 'subject' ? 2 : section === 'professional_summary' ? 4 : 12}
      />
      {error && <ErrorBox message={error} />}
      <div className="editor-actions">
        <span className="muted" role="status">
          {message}
        </span>
        <button className="button small" disabled={busy} onClick={() => action('regenerate')}>
          <RefreshCw size={14} /> Regenerate section
        </button>
        <button
          className="button small black"
          disabled={busy || !content.trim()}
          onClick={() => action('save')}
        >
          <Save size={14} /> Save & review
        </button>
      </div>
    </section>
  );
}
export default function Results({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [row, setRow] = useState<Analysis | null>(null);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('Match analysis');
  useEffect(() => {
    api
      .analysis(id)
      .then(setRow)
      .catch((e) => setError(e.message));
  }, [id]);
  if (!row)
    return error ? (
      <ErrorBox message={error} />
    ) : (
      <p className="loading-copy">Opening your analysis…</p>
    );
  const { matching, resume, job, application, review, events } = row.result;
  const tabs = ['Match analysis', 'Application studio', 'Interview prep', 'Agent workflow'];
  async function report() {
    try {
      await api.downloadReport(row!.id);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <>
      <Link href="/history" className="back-link">
        <ArrowLeft size={14} /> ALL OPPORTUNITIES
      </Link>
      <PageHeading
        eyebrow={row.company || 'YOUR ANALYSIS'}
        title={row.job_title}
        description={`Prepared for ${resume?.candidate_name || 'your candidate profile'} · ${new Date(row.created_at).toLocaleDateString('en-IN')} · ${row.result.mode === 'mock' ? 'Offline mock output' : 'Live AI output'}`}
        action={
          <button className="button black" onClick={report}>
            <Download size={16} /> Download report
          </button>
        }
      />
      {error && <ErrorBox message={error} />}
      {row.result.errors?.map((e, i) => (
        <ErrorBox key={i} message={e} />
      ))}
      <div className="review-banner">
        <div>
          <Check size={17} />
          <strong>Review outcome</strong>
          <StatusPill value={row.workflow_status} />
        </div>
        <span>
          {row.result.revision_count || 0} / 2 revisions · {review?.quality_score ?? '—'}/100 review
          quality
        </span>
      </div>
      {(review?.unsupported_claims.length || 0) > 0 && (
        <ErrorBox message={`Review flagged: ${review?.unsupported_claims.join('; ')}`} />
      )}
      <div className="tabs" role="tablist">
        {tabs.map((t) => (
          <button
            role="tab"
            aria-selected={tab === t}
            key={t}
            className={tab === t ? 'selected' : ''}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>
      {tab === 'Match analysis' && (
        <>
          <div className="score-layout">
            <section className="panel score-panel">
              <div>
                <span className="eyebrow">OVERALL COMPATIBILITY</span>
                <div className="large-score">
                  {row.match_score ?? '—'}
                  <span>/100</span>
                </div>
                <h3>
                  {row.match_score === null
                    ? 'Score unavailable'
                    : row.match_score >= 80
                      ? 'Strong documented alignment'
                      : row.match_score >= 50
                        ? 'A foundation to build on'
                        : 'Room to close the gaps'}
                </h3>
                <p>
                  A measure of resume evidence against this job.
                  <br />
                  This is not a probability of being hired.
                </p>
                {row.match_score === null && matching?.notice && <p>{matching.notice}</p>}
              </div>
              <div
                className="score-ring"
                style={{
                  background: `conic-gradient(#151515 ${(row.match_score || 0) * 3.6}deg, #ececea 0)`,
                }}
              >
                <span>
                  {row.match_score ?? '—'}
                  <small>COMPATIBILITY</small>
                </span>
              </div>
            </section>
            <section className="panel coverage-panel">
              <span className="eyebrow">THE SCORE, EXPLAINED</span>
              {Object.entries(matching?.breakdown || {}).map(([key, b]) => (
                <div className="coverage-row" key={key}>
                  <div>
                    <strong>
                      {key === 'alignment'
                        ? 'Experience & responsibilities'
                        : `${key} requirements`}
                    </strong>
                    <span>
                      {b.coverage === null ? 'Not applicable' : `${b.coverage.toFixed(0)}%`}
                    </span>
                  </div>
                  <div className="coverage-track">
                    <span style={{ width: `${b.coverage || 0}%` }} />
                  </div>
                  <small>
                    {b.count} requirements · {(b.weight * 100).toFixed(1)}% effective weight ·{' '}
                    {b.contribution.toFixed(1)} points
                  </small>
                </div>
              ))}
            </section>
          </div>
          <section className="panel">
            <div className="section-heading">
              <div>
                <h2>Every match needs evidence.</h2>
                <p>Direct 1.0 · Related 0.5 · Partial 0.25 · Missing or unknown 0.0</p>
              </div>
              <span className="pill">{matching?.requirements.length || 0} REQUIREMENTS</span>
            </div>
            <div className="table-scroll">
              <table className="evidence-table">
                <thead>
                  <tr>
                    <th>REQUIREMENT</th>
                    <th>MATCH</th>
                    <th>RESUME EVIDENCE</th>
                  </tr>
                </thead>
                <tbody>
                  {matching?.requirements.map((r, i) => (
                    <tr key={i}>
                      <td>
                        <strong>{r.requirement}</strong>
                        <span className="table-sub">{r.category}</span>
                      </td>
                      <td>
                        <StatusPill value={r.status} />
                      </td>
                      <td>
                        {r.evidence && <blockquote>{r.evidence}</blockquote>}
                        <span className="evidence-explanation">{r.explanation}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="panel-footnote">
              Base weights: mandatory 70%, preferred 20%, alignment 10%. Categories with no
              requirements are excluded and remaining weights are normalized.
            </div>
          </section>
          <div className="two-columns">
            <section className="panel padded">
              <h2>Where to focus next</h2>
              <BulletList items={matching?.recommendations || []} />
            </section>
            <section className="panel padded">
              <h2>Projects & experience</h2>
              <BulletList items={matching?.project_relevance || []} />
              <h3>Experience alignment</h3>
              <p className="body-copy">{matching?.experience_analysis}</p>
            </section>
          </div>
          <div className="two-columns">
            <section className="panel padded">
              <h2>Extracted candidate profile</h2>
              <div className="tags">
                {resume?.technical_skills.map((s) => (
                  <span className="pill" key={s}>
                    {s}
                  </span>
                ))}
              </div>
              <h3>Education</h3>
              <BulletList items={resume?.education || []} />
              <h3>Projects</h3>
              <BulletList items={resume?.projects || []} />
              <h3>Experience</h3>
              <BulletList items={resume?.experience || []} />
              <h3>Certifications</h3>
              <BulletList items={resume?.certifications || []} />
              <h3>Missing information</h3>
              <BulletList items={resume?.missing_information || []} />
            </section>
            <section className="panel padded">
              <h2>Extracted job requirements</h2>
              <h3>Mandatory skills</h3>
              <BulletList items={job?.required_skills || []} />
              <h3>Preferred skills</h3>
              <BulletList items={job?.preferred_skills || []} />
              <h3>Responsibilities</h3>
              <BulletList items={job?.responsibilities || []} />
              <h3>Ambiguities</h3>
              <BulletList items={job?.ambiguities || []} />
            </section>
          </div>
        </>
      )}
      {tab === 'Application studio' && application && (
        <>
          <div className="info-note">
            Edit and save any draft to run validation again. Confirm the source facts before
            submitting an application yourself.
          </div>
          <div className="editor-grid">
            {(Object.keys(sectionNames) as Section[]).map((s) => (
              <Editor key={s} row={row} section={s} onUpdate={setRow} />
            ))}
          </div>
          <div className="two-columns">
            <section className="panel padded">
              <h2>Resume improvements</h2>
              <BulletList items={application.resume_suggestions} />
              <h3>Project presentation</h3>
              <BulletList items={application.project_suggestions} />
            </section>
            <section className="panel padded">
              <h2>Supported keywords</h2>
              <div className="tags">
                {application.keywords.map((s) => (
                  <span className="pill" key={s}>
                    {s}
                  </span>
                ))}
              </div>
              <h3>Review notes</h3>
              <BulletList items={[...(review?.issues || []), ...(review?.suggestions || [])]} />
            </section>
          </div>
        </>
      )}
      {tab === 'Interview prep' && (
        <>
          <InterviewCoach key={id} analysisId={id} />
          <section className="panel padded">
            <span className="eyebrow">PRACTICE WITH PURPOSE</span>
            <h2>Be ready to explain your work.</h2>
            <p className="body-copy">
              Use these questions to discuss your projects, revise the role’s core skills and
              acknowledge learning gaps honestly.
            </p>
            <div className="question-list">
              {application?.interview_questions.map((q, i) => (
                <div key={i}>
                  <span>{String(i + 1).padStart(2, '0')}</span>
                  <p>{q}</p>
                </div>
              ))}
            </div>
            <button
              className="button"
              onClick={() =>
                downloadText(
                  application?.interview_questions.join('\n\n') || '',
                  'interview-preparation.txt',
                )
              }
            >
              <Download size={16} /> Download questions
            </button>
          </section>
        </>
      )}
      {tab === 'Agent workflow' && (
        <div className="two-columns">
          <section className="panel padded">
            <h2>Five agents. Shared context.</h2>
            <AgentMonitor events={events || []} />
            <h3>Review feedback</h3>
            <BulletList items={[...(review?.issues || []), ...(review?.suggestions || [])]} />
            <p className="body-copy">
              Resume and job analysis run in parallel. Matching joins both outputs. The generator
              and reviewer can loop for at most two revisions.
            </p>
          </section>
          <section className="panel padded">
            <h2>Execution timeline</h2>
            <div className="event-log">
              {events?.map((e, i) => (
                <div key={i}>
                  <span className="mono">
                    {e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : '—'}
                  </span>
                  <strong>{e.type.replaceAll('_', ' ')}</strong>
                  {e.duration_ms !== undefined && <small>{e.duration_ms} ms</small>}
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </>
  );
}
