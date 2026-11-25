'use client';

import { useEffect, useRef, useState } from 'react';

import { ErrorBox } from '@/components/ui/shared';

import { interviewApi, type Interview, type InterviewSummary } from './api';
import InterviewReport from './report';
import { speakQuestion, useVoiceAnswer } from './use-voice-answer';

export default function InterviewCoach({ analysisId }: { analysisId: string }) {
  const [interview, setInterview] = useState<Interview | null>(null);
  const [saved, setSaved] = useState<InterviewSummary[]>([]);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const mounted = useRef(false);
  const voice = useVoiceAnswer(setDraft, setError);
  const disabled = busy || voice.phase !== 'idle';
  const sessionOpen = interview !== null;

  useEffect(() => {
    mounted.current = true;
    window.speechSynthesis?.getVoices();
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    if (sessionOpen) return;
    let active = true;
    interviewApi.list(analysisId).then(
      (items) => {
        if (active) setSaved(items);
      },
      (err: Error) => {
        if (active) setError(err.message);
      },
    );
    return () => {
      active = false;
    };
  }, [analysisId, sessionOpen]);

  function readQuestion(text: string) {
    if (!speakQuestion(text)) {
      setNotice(
        'A local browser voice is unavailable. You can still read the question and record an answer.',
      );
    }
  }

  async function update(operation: () => Promise<Interview>, readAloud = false) {
    setError('');
    setNotice('');
    setBusy(true);
    try {
      const next = await operation();
      if (!mounted.current) return;
      setInterview(next);
      setDraft('');
      if (readAloud && next.question) readQuestion(next.question.text);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const question = interview?.question;

  return (
    <section className="panel padded" aria-label="Voice interview coach">
      <span className="eyebrow">MOCK INTERVIEW</span>
      <h2>Practise with a voice interviewer.</h2>
      <p className="body-copy">
        Answer at least ten main questions tailored to this resume and role. Follow-ups are extra.
        Review the transcript before sending each answer.
      </p>
      {error && <ErrorBox message={error} />}
      {notice && <p role="status">{notice}</p>}
      {busy && <p role="status">Working on your interview…</p>}
      {interview && (
        <button
          className="button"
          disabled={disabled}
          onClick={() => {
            window.speechSynthesis?.cancel();
            setInterview(null);
            setDraft('');
            setError('');
            setNotice('');
          }}
        >
          Back to saved sessions
        </button>
      )}

      {!interview && (
        <>
          <button
            className="button black"
            disabled={disabled}
            onClick={() => update(() => interviewApi.start(analysisId), true)}
          >
            Start voice interview
          </button>
          {saved.length > 0 && (
            <div className="question-list">
              <h3>Saved sessions</h3>
              {saved.map((item) => (
                <button
                  key={item.id}
                  className="button"
                  disabled={disabled}
                  onClick={() => update(() => interviewApi.open(item.id))}
                >
                  {item.completed ? 'View report' : 'Resume session'} ·{' '}
                  {new Date(item.created_at).toLocaleString()}
                </button>
              ))}
            </div>
          )}
        </>
      )}

      {interview && question && (
        <div>
          <p aria-live="polite">
            {interview.answered}/{interview.total} main questions answered
          </p>
          <h3>
            {question.follow_up ? 'Follow-up to question' : 'Question'} {question.number}
          </h3>
          <p>{question.text}</p>
          <button
            className="button"
            disabled={disabled}
            onClick={() => readQuestion(question.text)}
          >
            Read question aloud
          </button>
          {voice.phase === 'recording' ? (
            <button className="button black" onClick={voice.stop}>
              Stop recording
            </button>
          ) : (
            <button
              className="button"
              disabled={disabled}
              onClick={() => {
                setError('');
                voice.start(interview.id);
              }}
            >
              {voice.phase === 'transcribing'
                ? 'Transcribing locally…'
                : voice.phase === 'microphone'
                  ? 'Waiting for microphone…'
                  : 'Record answer'}
            </button>
          )}
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (!disabled && draft.trim()) {
                window.speechSynthesis?.cancel();
                void update(
                  () => interviewApi.answer(interview.id, interview.version, draft.trim()),
                  true,
                );
              }
            }}
          >
            <label>
              Your answer or corrected transcript
              <textarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                maxLength={4000}
                rows={5}
                disabled={disabled}
              />
            </label>
            <button type="submit" className="button black" disabled={disabled || !draft.trim()}>
              Submit answer
            </button>
          </form>
        </div>
      )}

      {interview && !question && !interview.report && (
        <button
          className="button black"
          disabled={disabled}
          onClick={() => update(() => interviewApi.report(interview.id))}
        >
          Generate interview report
        </button>
      )}

      {interview && <InterviewReport interview={interview} />}

      {!!interview?.turns.length && (
        <details>
          <summary>Saved transcript</summary>
          <ol>
            {interview.turns.map((turn, index) => (
              <li key={index}>
                <strong>
                  {turn.follow_up ? 'Follow-up' : 'Question'} {turn.number}
                </strong>
                <p>{turn.question}</p>
                <p>{turn.answer}</p>
              </li>
            ))}
          </ol>
        </details>
      )}
    </section>
  );
}
