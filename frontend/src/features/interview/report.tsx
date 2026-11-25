import { BulletList } from '@/components/ui/shared';

import type { Interview } from './api';

export default function InterviewReport({ interview }: { interview: Interview }) {
  const report = interview.report;
  if (!report) return null;

  return (
    <div>
      <h3>Interview feedback</h3>
      <p className="body-copy">{report.summary}</p>
      <div className="question-list">
        {report.feedback.map((feedback) => (
          <article key={feedback.number}>
            <h4>
              Question {feedback.number} · {feedback.rating}/4
            </h4>
            <p>{interview.turns.find((turn) => turn.number === feedback.number)?.question}</p>
            <p>
              <strong>Strength:</strong> {feedback.strength}
            </p>
            <p>
              <strong>Try next:</strong> {feedback.improvement}
            </p>
            {feedback.evidence && <blockquote>{feedback.evidence}</blockquote>}
          </article>
        ))}
      </div>
      <h3>Practice next</h3>
      <BulletList items={report.practice_tasks} />
    </div>
  );
}
