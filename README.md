# 🎬 Transkriptor

Ferramenta offline para transcrever vídeos de processos e extrair frames automaticamente, gerando insumos prontos para serem analisados pelo **Claude (Anthropic)**.

> Ideal para documentar processos em sistemas, gerar manuais, levantar requisitos e criar tutoriais a partir de gravações de tela.

---

## 💡 Intuito

Muitas vezes temos gravações de processos — como um fluxo dentro de um sistema — onde alguém explica em voz o que está fazendo na tela. O **Transkriptor** resolve o problema de enviar esse vídeo para uma IA analisar, já que ferramentas como o Claude ainda não aceitam vídeo diretamente.

O script faz três coisas:
1. **Extrai frames** do vídeo em intervalos regulares (prints das telas)
2. **Transcreve o áudio** completamente offline, sem enviar nada para a internet
3. **Identifica quem está falando** em cada trecho (Falante 1, Falante 2...) — *opcional*, útil para reuniões com várias pessoas

Com esses dois insumos em mãos, você envia para o Claude e pede o que precisar: documentação, passo a passo, requisitos funcionais, manual do usuário, etc.

---

## 🖥️ Pré-requisitos

### 1. Python 3
Verifique se já tem instalado:
```bash
python3 --version
```

Se não tiver, baixe em: [python.org/downloads](https://www.python.org/downloads/)

---

### 2. FFmpeg
Necessário para o Whisper processar o áudio do vídeo.

**Mac:**
```bash
brew install ffmpeg
```

> Não tem Homebrew? Instale primeiro:
> ```bash
> /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
> ```

**Linux:**
```bash
sudo apt install ffmpeg
```

**Windows:**
Baixe em [ffmpeg.org/download.html](https://ffmpeg.org/download.html) e adicione ao PATH.

---

### 3. Dependências Python
```bash
pip3 install openai-whisper opencv-python pillow tqdm
```

> ⚠️ O modelo do Whisper é baixado automaticamente na primeira execução (~150MB a ~1.4GB dependendo do modelo escolhido).

---

### 4. pyannote (opcional — identificação de falantes)
> Só é necessário se você for usar `DIARIZATION = True`. No padrão (`False`), a transcrição é feita só com o Whisper e você pode pular este passo e o próximo.

O [pyannote](https://github.com/pyannote/pyannote-audio) é quem descobre **quem está falando** em cada trecho. Instale com:
```bash
pip3 install "pyannote.audio<4"
```

> ℹ️ O `<4` é proposital: a versão 4 do pyannote mudou a API e exige Python 3.10+. O script usa a versão 3.x.

Confira se instalou (deve mostrar `Version: 3.x`):
```bash
pip3 show pyannote.audio
```

---

### 5. Token do Hugging Face (opcional — para baixar os modelos do pyannote)
Os modelos do pyannote (~30 MB) ficam no Hugging Face e exigem aceite dos termos de uso. **O token só é usado no primeiro download** — depois disso tudo roda offline.

1. Crie uma conta em [huggingface.co](https://huggingface.co)
2. Aceite os termos nas duas páginas (preencha o formulário e clique em *Agree and access repository*):
   - [pyannote/segmentation-3.0](https://hf.co/pyannote/segmentation-3.0)
   - [pyannote/speaker-diarization-3.1](https://hf.co/pyannote/speaker-diarization-3.1)
3. Crie um token do tipo *Read* em [hf.co/settings/tokens](https://hf.co/settings/tokens)
4. Salve o token no computador (cole o token quando for pedido):
```bash
python3 -c "from huggingface_hub import login; login()"
```

> Prefere não salvar? Rode `export HF_TOKEN=hf_seu_token_aqui` no mesmo terminal antes de rodar o script (vale só para aquela janela do terminal).

Pronto: coloque `DIARIZATION = True` no `index.py` e, na primeira vez que rodar, os modelos são baixados automaticamente.

---

## 🚀 Como usar

### 1. Clone ou baixe o projeto
```bash
git clone https://github.com/victorreinor/transkriptor.git
cd transkriptor
```

### 2. Coloque seu vídeo na pasta do projeto
```
transkriptor/
├── index.py
├── meu_video.mp4   ← aqui
└── output/
```

### 3. Ajuste as configurações no topo do `index.py`
Veja a seção de [Parametrizações](#-parametrizações) abaixo.

### 4. Rode o script
```bash
python3 index.py
```

### 5. Pegue os arquivos gerados na pasta `output/`
```
output/
├── transcricao.txt         ← transcrição completa com timestamps
├── frame_0000_0.0s.jpg     ← prints das telas extraídos
├── frame_0001_5.0s.jpg
└── ...
```

### 6. Envie para o Claude
- Anexe o `transcricao.txt`, que fica assim:
  ```
  [12.4s - 18.0s] Agora eu clico em "Novo pedido" e preencho o cliente.
  [18.2s - 21.5s] E esse campo de prazo é obrigatório?
  ```
  Com `DIARIZATION = True`, cada trecho também indica quem falou:
  ```
  [12.4s - 18.0s] Falante 1: Agora eu clico em "Novo pedido" e preencho o cliente.
  [18.2s - 21.5s] Falante 2: E esse campo de prazo é obrigatório?
  ```
- Anexe os frames mais relevantes
- Diga o que quer: *"Gera uma documentação desse processo"*, *"Cria um passo a passo"*, *"Levanta os requisitos funcionais"*, etc.

---

## ⚙️ Parametrizações

Todas as configurações ficam no topo do arquivo `index.py`:

```python
VIDEO_PATH = "seu_video.mp4"
```
Caminho para o vídeo. Pode ser o nome do arquivo (se estiver na mesma pasta) ou o caminho completo, ex: `/Users/nome/Downloads/video.mp4`.

---

```python
OUTPUT_DIR = "output"
```
Pasta onde os frames e a transcrição serão salvos. Criada automaticamente se não existir.

---

```python
FRAME_INTERVAL = 5
```
Intervalo em segundos entre cada frame capturado. Aumente para vídeos longos e diminua para processos mais detalhados.

| Valor | Uso recomendado |
|-------|----------------|
| `2` | Processos rápidos com muitas telas |
| `5` | Padrão — bom equilíbrio |
| `10` | Vídeos longos (+20 min) |
| `15` | Apenas visão geral do processo |

---

```python
WHISPER_MODEL = "small"
```
Modelo do Whisper usado na transcrição. Modelos maiores são mais precisos, porém mais lentos.

| Modelo | Tamanho | Velocidade (CPU) | Precisão |
|--------|---------|-----------------|---------|
| `tiny` | 75 MB | ⚡⚡⚡⚡ muito rápido | baixa |
| `base` | 145 MB | ⚡⚡⚡ rápido | boa |
| `small` | 465 MB | ⚡⚡ médio | boa ✅ recomendado |
| `medium` | 1.4 GB | ⚡ lento | ótima |
| `large` | 2.9 GB | 🐢 muito lento | máxima |

---

```python
LANGUAGE = "pt"
```
Idioma do áudio. Ajuda o Whisper a ser mais preciso.

| Valor | Idioma |
|-------|--------|
| `pt` | Português |
| `en` | Inglês |
| `es` | Espanhol |

---

```python
DIARIZATION = False
```
Identifica quem está falando em cada trecho usando o pyannote.

| Valor | Comportamento |
|-------|---------------|
| `False` | Padrão — transcrição só com o Whisper, sem identificar falantes (não precisa do pyannote) |
| `True` | Identifica os falantes como `Falante 1`, `Falante 2`... na ordem em que falam pela primeira vez — basta dizer ao Claude quem é quem. Requer os passos [4](#4-pyannote-opcional--identificação-de-falantes) e [5](#5-token-do-hugging-face-opcional--para-baixar-os-modelos-do-pyannote) dos pré-requisitos |

> No Mac com Apple Silicon usa a GPU (MPS) automaticamente. Leva cerca de 20% da duração do vídeo (ex: ~10 min para 50 min de vídeo).

---

```python
NUM_SPEAKERS = None
```
Só vale com `DIARIZATION = True`. Quantidade de pessoas que falam no vídeo. Se você souber, informe (ex: `3`) — isso melhora a precisão. Com `None`, o número é detectado automaticamente.

---

## 📁 Estrutura do projeto

```
transkriptor/
├── index.py        # script principal
├── README.md       # este arquivo
└── output/         # gerada automaticamente ao rodar
    ├── transcricao.txt
    └── frame_XXXX_XXs.jpg
```

---

## 🔒 Privacidade

Todo o processamento é feito **100% offline**, localmente na sua máquina. Nenhum dado do vídeo, áudio ou transcrição é enviado para a internet. A internet só é usada no primeiro uso, para baixar os modelos do Whisper (e do pyannote, se `DIARIZATION = True`).

---

## 🛠️ Tecnologias utilizadas

- [Whisper (OpenAI)](https://github.com/openai/whisper) — transcrição de áudio offline
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) — identificação de falantes (diarização)
- [OpenCV](https://opencv.org/) — extração de frames do vídeo
- [tqdm](https://github.com/tqdm/tqdm) — barra de progresso no terminal
- [FFmpeg](https://ffmpeg.org/) — processamento de áudio/vídeo
