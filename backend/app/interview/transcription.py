from functools import lru_cache
from io import BytesIO
from threading import Lock

from app.core.config import ROOT

MAX_AUDIO_BYTES = 8 * 1024 * 1024
MAX_AUDIO_SECONDS = 180
_model_lock = Lock()


class AudioError(ValueError):
    pass


@lru_cache(maxsize=1)
def whisper_model():
    from faster_whisper import WhisperModel

    return WhisperModel(
        "base", device="cpu", compute_type="int8", download_root=str(ROOT.parent / ".local/whisper")
    )


def transcribe(data: bytes) -> str:
    import av
    import numpy as np

    if not data or len(data) > MAX_AUDIO_BYTES:
        raise AudioError("Record a non-empty answer under 8 MB.")

    chunks = []
    samples = 0
    resampler = av.AudioResampler(format="fltp", layout="mono", rate=16000)
    try:
        with av.open(BytesIO(data)) as recording:
            for frame in recording.decode(audio=0):
                for converted in resampler.resample(frame):
                    samples += converted.samples
                    if samples > 16000 * MAX_AUDIO_SECONDS:
                        raise AudioError("Record an answer of three minutes or less.")
                    chunks.append(converted.to_ndarray().reshape(-1))
    except (av.FFmpegError, IndexError) as exc:
        raise AudioError("This recording could not be read. Try recording again.") from exc

    if not chunks:
        raise AudioError("No audio was detected. Check your microphone.")

    with _model_lock:
        segments, _ = whisper_model().transcribe(np.concatenate(chunks), vad_filter=True)
        transcript = " ".join(segment.text.strip() for segment in segments).strip()

    if not transcript:
        raise AudioError("No speech was detected. Try again or type your answer.")
    return transcript[:4000]
