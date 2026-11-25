import { useEffect, useRef, useState } from 'react';

import { interviewApi } from './api';

type Phase = 'idle' | 'microphone' | 'recording' | 'transcribing';

export function useVoiceAnswer(onText: (text: string) => void, onError: (message: string) => void) {
  const [phase, setPhase] = useState<Phase>('idle');
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mounted = useRef(false);

  function releaseMicrophone() {
    if (timer.current !== null) clearTimeout(timer.current);
    timer.current = null;
    stream.current?.getTracks().forEach((track) => track.stop());
    stream.current = null;
    recorder.current = null;
  }

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      if (recorder.current) {
        recorder.current.onstop = null;
        if (recorder.current.state === 'recording') recorder.current.stop();
      }
      releaseMicrophone();
      window.speechSynthesis?.cancel();
    };
  }, []);

  async function start(interviewId: string) {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      onError('Microphone recording is unavailable in this browser. You can type your answer.');
      return;
    }

    window.speechSynthesis?.cancel();
    setPhase('microphone');
    try {
      const microphone = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!mounted.current) {
        microphone.getTracks().forEach((track) => track.stop());
        return;
      }

      stream.current = microphone;
      const capture = new MediaRecorder(microphone);
      recorder.current = capture;
      const chunks: Blob[] = [];
      capture.ondataavailable = (event) => {
        if (event.data.size) chunks.push(event.data);
      };
      capture.onerror = () => {
        capture.onstop = null;
        releaseMicrophone();
        setPhase('idle');
        onError('Recording failed. Try again or type your answer.');
      };
      capture.onstop = async () => {
        releaseMicrophone();
        setPhase('transcribing');
        try {
          const result = await interviewApi.transcribe(
            interviewId,
            new Blob(chunks, { type: capture.mimeType }),
          );
          if (mounted.current) onText(result.text);
        } catch (error) {
          if (mounted.current) onError((error as Error).message);
        } finally {
          if (mounted.current) setPhase('idle');
        }
      };
      capture.start();
      setPhase('recording');
      timer.current = setTimeout(() => {
        if (capture.state === 'recording') capture.stop();
      }, 175_000);
    } catch {
      releaseMicrophone();
      if (mounted.current) {
        setPhase('idle');
        onError('Could not open the microphone. Check browser permissions or type your answer.');
      }
    }
  }

  function stop() {
    if (recorder.current?.state === 'recording') recorder.current.stop();
  }

  return { phase, start, stop };
}

export function speakQuestion(text: string) {
  if (!window.speechSynthesis || typeof SpeechSynthesisUtterance === 'undefined') return false;

  const synthesis = window.speechSynthesis;
  const voices = synthesis.getVoices();
  const voice =
    voices.find((item) => item.localService && /^en\b/i.test(item.lang)) ??
    voices.find((item) => item.localService);

  // A browser default can be backed by a remote service.
  if (!voice) return false;
  synthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.voice = voice;
  utterance.lang = voice.lang;
  synthesis.speak(utterance);
  return true;
}
