'use client';
import { Check, Circle, LoaderCircle, X } from 'lucide-react';
import type { AgentEvent } from '@/types';
const nodes = [
  ['parsing', 'Document parser', 'Extract readable source text'],
  ['resume_analyzer', 'Resume analyzer', 'Build the candidate profile'],
  ['jd_analyzer', 'Job description analyzer', 'Understand the requirements'],
  ['matching', 'Resume matching agent', 'Compare with source evidence'],
  ['generation', 'Application generator', 'Write a tailored application'],
  ['review', 'Review & validation', 'Check claims and quality'],
];
export default function AgentMonitor({
  events,
  running = false,
}: {
  events: AgentEvent[];
  running?: boolean;
}) {
  return (
    <div className="agent-monitor">
      {nodes.map(([id, title, desc], i) => {
        const related = events.filter((e) => e.node === id);
        const last = related.at(-1);
        const done = last?.type.endsWith('_completed');
        const failed = last?.type.endsWith('_failed');
        const active = last?.type.endsWith('_started') && running;
        return (
          <div className={`agent-row ${active ? 'executing' : ''}`} key={id}>
            <span className="agent-number">{String(i + 1).padStart(2, '0')}</span>
            <div className={`agent-state ${done ? 'done' : ''}`}>
              {done ? (
                <Check size={14} />
              ) : failed ? (
                <X size={14} />
              ) : active ? (
                <LoaderCircle size={14} className="spin" />
              ) : (
                <Circle size={8} />
              )}
            </div>
            <div>
              <strong>{title}</strong>
              <span>
                {desc}
                {id === 'jd_analyzer' || id === 'resume_analyzer' ? ' · parallel' : ''}
              </span>
            </div>
            <span className="agent-time">
              {done
                ? `${last?.duration_ms?.toFixed(0) ?? '—'} ms`
                : failed
                  ? 'Failed'
                  : active
                    ? 'Running'
                    : 'Waiting'}
            </span>
          </div>
        );
      })}
      <div className="monitor-footer">
        <span className="tiny-dot" /> EVENTS FROM THE RUNNING LANGGRAPH WORKFLOW
      </div>
    </div>
  );
}
