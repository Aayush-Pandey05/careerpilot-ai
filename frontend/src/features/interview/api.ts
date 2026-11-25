import { request } from '@/lib/api';

export type InterviewTurn = {
  number: number;
  question: string;
  answer: string;
  follow_up: boolean;
};

export type Interview = {
  id: string;
  version: number;
  answered: number;
  total: number;
  question: { number: number; text: string; follow_up: boolean } | null;
  turns: InterviewTurn[];
  report: {
    summary: string;
    feedback: {
      number: number;
      rating: number;
      evidence: string;
      strength: string;
      improvement: string;
    }[];
    practice_tasks: string[];
  } | null;
};

export type InterviewSummary = { id: string; created_at: string; completed: boolean };

export const interviewApi = {
  list: (analysisId: string) => request<InterviewSummary[]>(`/interviews/analysis/${analysisId}`),
  start: (analysisId: string) =>
    request<Interview>(`/interviews/analysis/${analysisId}`, { method: 'POST' }),
  open: (id: string) => request<Interview>(`/interviews/${id}`),
  transcribe: (id: string, blob: Blob) => {
    const form = new FormData();
    form.append('audio', blob, 'answer');
    return request<{ text: string }>(`/interviews/${id}/transcription`, {
      method: 'POST',
      body: form,
    });
  },
  answer: (id: string, version: number, text: string) =>
    request<Interview>(`/interviews/${id}/answers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ version, text }),
    }),
  report: (id: string) => request<Interview>(`/interviews/${id}/report`, { method: 'POST' }),
};
