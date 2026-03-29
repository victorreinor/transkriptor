"""
Transcrição offline de vídeo com Whisper + extração de frames
Requisitos:
    pip install openai-whisper opencv-python pillow
    
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


def transcribe_audio(video_path, language="pt", model_name="medium"):
    """Transcreve o áudio do vídeo com Whisper (offline)."""
    print(f"Carregando modelo Whisper '{model_name}'...")
    model = whisper.load_model(model_name)

    print("Transcrevendo áudio (pode demorar alguns minutos)...")
    result = model.transcribe(video_path, language=language, verbose=False)
    return result


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
            f.write(f"[{start:.1f}s - {end:.1f}s] {text}\n")

        f.write("\n\n--- FRAMES CAPTURADOS ---\n\n")
        for frame in frames_info:
            f.write(f"Frame em {frame['timestamp']:.1f}s → {frame['file']}\n")

        f.write("\n\n--- TRANSCRIÇÃO COMPLETA ---\n\n")
        f.write(result["text"])

    print(f"✅ Transcrição salva em '{output_path}'")
    return output_path


if __name__ == "__main__":
    # 1. Extrai frames
    frames_info = extract_frames(VIDEO_PATH, OUTPUT_DIR, FRAME_INTERVAL)

    # 2. Transcreve o áudio
    result = transcribe_audio(VIDEO_PATH, language=LANGUAGE, model_name=WHISPER_MODEL)

    # 3. Salva tudo em um arquivo .txt
    save_transcription(result, frames_info, OUTPUT_DIR)

    print("\n✅ Processo concluído!")
    print(f"→ Frames e transcrição salvos na pasta '{OUTPUT_DIR}/'")
    print("→ Envie o arquivo 'transcricao.txt' + os frames para o Claude!")
