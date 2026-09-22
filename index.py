"""
Transcrição offline de vídeo com Whisper + extração de frames (+ identificação de falantes opcional)
Requisitos:
    pip install openai-whisper opencv-python pillow
    pip install "pyannote.audio<4"   # só se DIARIZATION = True

    Também precisa do ffmpeg instalado no sistema:
    - Windows: https://ffmpeg.org/download.html
    - Mac: brew install ffmpeg
    - Linux: sudo apt install ffmpeg
"""

import whisper
import cv2
import os
from PIL import Image

VIDEO_PATH = "natanael.mp4"   # <- coloque o caminho do seu vídeo
OUTPUT_DIR = "output"          # pasta onde serão salvos os frames e a transcrição
FRAME_INTERVAL = 5             # captura 1 frame a cada X segundos
WHISPER_MODEL = "small"       # opções: tiny, base, small, medium, large (maior = mais preciso e lento)
LANGUAGE = "pt"                # idioma do áudio
DIARIZATION = False            # True = identifica quem está falando em cada trecho (pyannote)
NUM_SPEAKERS = None            # só com DIARIZATION = True: quantidade de pessoas no vídeo, se souber. None = detecta sozinho

os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_frames(video_path, output_dir, interval_seconds=5):
    """Extrai frames do vídeo em intervalos regulares."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * interval_seconds)
    
    frames_info = []
    frame_count = 0
    saved_count = 0

    print(f"Extraindo frames a cada {interval_seconds}s...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            timestamp = frame_count / fps
            filename = f"frame_{saved_count:04d}_{timestamp:.1f}s.jpg"
            filepath = os.path.join(output_dir, filename)
            cv2.imwrite(filepath, frame)
            frames_info.append({"file": filename, "timestamp": timestamp})
            saved_count += 1

        frame_count += 1

    cap.release()
    print(f"✅ {saved_count} frames extraídos em '{output_dir}/'")
    return frames_info


def transcribe_audio(audio, language="pt", model_name="medium", word_timestamps=False):
    """Transcreve o áudio do vídeo com Whisper (offline)."""
    print(f"Carregando modelo Whisper '{model_name}'...")
    model = whisper.load_model(model_name)

    print("Transcrevendo áudio (pode demorar alguns minutos)...")
    result = model.transcribe(audio, language=language, verbose=False, word_timestamps=word_timestamps)
    return result


def diarize_audio(audio, num_speakers=None):
    """Identifica os trechos de fala de cada pessoa com pyannote (offline após o 1º download)."""
    import torch
    from pyannote.audio import Pipeline
    from pyannote.audio.core.task import Specifications, Problem, Resolution

    # PyTorch 2.6+ bloqueia por padrão o carregamento dos checkpoints do pyannote 3.x
    torch.serialization.add_safe_globals([torch.torch_version.TorchVersion, Specifications, Problem, Resolution])

    print("Carregando modelo de diarização (pyannote)...")
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
    if pipeline is None:
        raise SystemExit(
            "❌ Não foi possível baixar o modelo do pyannote. Aceite os termos em "
            "https://hf.co/pyannote/speaker-diarization-3.1 e https://hf.co/pyannote/segmentation-3.0 "
            "e defina seu token com 'export HF_TOKEN=hf_...' (veja o passo 5 do README)."
        )

    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    pipeline.to(torch.device(device))

    print(f"Identificando falantes (pode demorar alguns minutos, usando {device})...")
    waveform = torch.from_numpy(audio).unsqueeze(0)
    diarization = pipeline({"waveform": waveform, "sample_rate": whisper.audio.SAMPLE_RATE}, num_speakers=num_speakers)
    return [(turn.start, turn.end, speaker) for turn, _, speaker in diarization.itertracks(yield_label=True)]


def speaker_at(start, end, turns):
    """Retorna quem mais fala no intervalo, ou None se ninguém fala nele."""
    overlap = {}
    for turn_start, turn_end, speaker in turns:
        duration = min(end, turn_end) - max(start, turn_start)
        if duration > 0:
            overlap[speaker] = overlap.get(speaker, 0) + duration
    return max(overlap, key=overlap.get) if overlap else None


def assign_speakers(segments, turns):
    """Atribui um falante a cada palavra e quebra os trechos sempre que o falante muda."""
    names = {}
    speaker_segments = []
    for seg in segments:
        for i, word in enumerate(seg["words"]):
            label = speaker_at(word["start"], word["end"], turns)
            if label is not None:
                speaker = names.setdefault(label, f"Falante {len(names) + 1}")
            elif speaker_segments:
                speaker = speaker_segments[-1]["speaker"]  # palavra num silêncio: mantém o falante anterior
            else:
                speaker = "Falante ?"

            last = speaker_segments[-1] if speaker_segments else None
            if i > 0 and last["speaker"] == speaker:
                last["end"] = word["end"]
                last["text"] += word["word"]
            else:
                speaker_segments.append({"start": word["start"], "end": word["end"], "text": word["word"], "speaker": speaker})

    print(f"✅ {len(names)} falante(s) identificado(s)")
    return speaker_segments


def save_transcription(result, frames_info, output_dir):
    """Salva a transcrição em formato legível com timestamps."""
    output_path = os.path.join(output_dir, "transcricao.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("TRANSCRIÇÃO DO VÍDEO\n")
        f.write("=" * 60 + "\n\n")

        # Transcrição por segmento com timestamp
        f.write("--- TRANSCRIÇÃO COM TIMESTAMPS ---\n\n")
        for seg in result["segments"]:
            start = seg["start"]
            end = seg["end"]
            text = seg["text"].strip()
            speaker = f"{seg['speaker']}: " if "speaker" in seg else ""
            f.write(f"[{start:.1f}s - {end:.1f}s] {speaker}{text}\n")

        f.write("\n\n--- FRAMES CAPTURADOS ---\n\n")
        for frame in frames_info:
            f.write(f"Frame em {frame['timestamp']:.1f}s → {frame['file']}\n")

        f.write("\n\n--- TRANSCRIÇÃO COMPLETA ---\n\n")
        if any("speaker" in seg for seg in result["segments"]):
            # Junta falas seguidas da mesma pessoa em um único parágrafo
            current_speaker = None
            for seg in result["segments"]:
                speaker = seg["speaker"]
                if speaker != current_speaker:
                    prefix = "\n\n" if current_speaker else ""
                    f.write(f"{prefix}{speaker}:")
                    current_speaker = speaker
                f.write(f" {seg['text'].strip()}")
        else:
            f.write(result["text"])

    print(f"✅ Transcrição salva em '{output_path}'")
    return output_path


if __name__ == "__main__":
    # 1. Extrai frames
    frames_info = extract_frames(VIDEO_PATH, OUTPUT_DIR, FRAME_INTERVAL)

    # 2. Transcreve o áudio
    audio = whisper.load_audio(VIDEO_PATH)
    result = transcribe_audio(audio, language=LANGUAGE, model_name=WHISPER_MODEL, word_timestamps=DIARIZATION)

    # 3. Identifica quem está falando em cada trecho
    if DIARIZATION:
        turns = diarize_audio(audio, num_speakers=NUM_SPEAKERS)
        result["segments"] = assign_speakers(result["segments"], turns)

    # 4. Salva tudo em um arquivo .txt
    save_transcription(result, frames_info, OUTPUT_DIR)

    print("\n✅ Processo concluído!")
    print(f"→ Frames e transcrição salvos na pasta '{OUTPUT_DIR}/'")
    print("→ Envie o arquivo 'transcricao.txt' + os frames para o Claude!")
