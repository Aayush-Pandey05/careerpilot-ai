import type { Analysis, AgentEvent, Health } from '@/types';
export const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function check(response: Response) {
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(
      typeof data.detail === 'string'
        ? data.detail
        : 'The request could not be processed. Check your inputs and backend.',
    );
  }
  return response;
}
export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await check(await fetch(API + path, { cache: 'no-store', ...options }));
  return response.status === 204 ? (undefined as T) : response.json();
}
export const api = {
  health: () => request<Health>('/health'),
  history: () => request<Analysis[]>('/analyses'),
  analysis: (id: string) => request<Analysis>(`/analyses/${encodeURIComponent(id)}`),
  remove: (id: string) => request<void>(`/analyses/${id}`, { method: 'DELETE' }),
  status: (id: string, status: string) =>
    request(`/applications/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    }),
  edit: (id: string, section: string, content: string) =>
    request<Analysis>(`/analyses/${id}/sections/${section}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    }),
  regenerate: (id: string, section: string) =>
    request<Analysis>(`/analyses/${id}/sections/${section}/regenerate`, { method: 'POST' }),
  downloadReport: async (id: string) => {
    const response = await check(await fetch(`${API}/analyses/${id}/report`));
    const url = URL.createObjectURL(await response.blob());
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'careerpilot-report.pdf';
    anchor.click();
    URL.revokeObjectURL(url);
  },
  report: (id: string) => `${API}/analyses/${id}/report`,
};

export async function analyzeStream(
  form: FormData,
  onEvent: (event: AgentEvent) => void,
  signal: AbortSignal,
) {
  const response = await check(
    await fetch(`${API}/analyses/stream`, { method: 'POST', body: form, signal }),
  );
  const reader = response.body?.getReader();
  if (!reader) throw new Error('Streaming is unavailable in this browser.');
  const decoder = new TextDecoder();
  let buffer = '';
  let terminal = false;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split('\n\n');
    buffer = frames.pop() || '';
    for (const frame of frames) {
      const data = frame
        .split('\n')
        .filter((l) => l.startsWith('data: '))
        .map((l) => l.slice(6))
        .join('\n');
      if (!data) continue;
      const event: AgentEvent = JSON.parse(data);
      onEvent(event);
      if (event.type === 'workflow_completed') terminal = true;
      if (event.type === 'workflow_failed') {
        terminal = true;
        if (!event.analysis) throw new Error(event.message || 'Workflow failed.');
      }
    }
  }
  if (!terminal)
    throw new Error(
      'Connection closed before the workflow completed. Check history before retrying.',
    );
}

export function downloadText(content: string, filename: string) {
  const url = URL.createObjectURL(new Blob([content], { type: 'text/plain;charset=utf-8' }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
