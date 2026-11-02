# Lunaria Open TTS

[Português (pt-BR)](README.pt-BR.md)

A small, self-hosted text-to-speech HTTP service for **Brazilian Portuguese**, running on CPU only.
It wraps two open-source TTS engines behind one FastAPI endpoint:

- **[Piper](https://github.com/rhasspy/piper)**: fast ONNX voices, called through the `piper` CLI.
- **[Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)**: a more natural-sounding PyTorch model, called through the `kokoro` Python package.

You send text and a voice id, and you get back a WAV file. It is the default TTS engine of **Lunaria**, a web tabletop RPG with an AI game master (see [Used in production](#used-in-production-by-lunaria)).

## How it works

- Voices are declared in `.env` as a JSON list (`PIPER_VOICES_JSON`). Each entry picks a backend: `piper` or `kokoro`.
- **Piper**: each request starts one `piper` process. It writes a temporary WAV file, which is read back and deleted.
- **Kokoro**: the pipeline for Portuguese (`lang_code="p"`) is loaded on the first request and then stays in memory. The audio chunks are joined and written as a 24 kHz WAV.
- No GPU and no paid API. At synthesis time everything runs locally. Kokoro downloads its weights from the Hugging Face Hub on first use and reads them from the local cache after that.

## Voices

These are the voices configured in production:

| `voice_id` | Engine | Upstream voice | Output |
|---|---|---|---|
| `pt-br-kokoro-santa` | Kokoro-82M v1.0 | `pm_santa` (male) | 24 kHz, 16-bit mono |
| `pt-br-kokoro-alex` | Kokoro-82M v1.0 | `pm_alex` (male) | 24 kHz, 16-bit mono |
| `pt-br-kokoro-dora` | Kokoro-82M v1.0 | `pf_dora` (female) | 24 kHz, 16-bit mono |
| `pt-br-faber-medium` | Piper | `pt_BR-faber-medium` | 22.05 kHz, 16-bit mono |
| `pt-br-cadu-medium` | Piper | `pt_BR-cadu-medium` | 22.05 kHz, 16-bit mono |
| `pt-br-jeff-medium` | Piper | `pt_BR-jeff-medium` | 22.05 kHz, 16-bit mono |
| `pt-br-edresson-low` | Piper | `pt_BR-edresson-low` | 16 kHz, 16-bit mono |

Any other Piper or Kokoro voice can be added through `.env`. Check its license first (see [Voice model licenses](#voice-model-licenses)).

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service status and number of configured voices |
| `GET` | `/voices` | Configured voices (`voice_id`, `name`, `language`, `provider`) |
| `POST` | `/generate` | Synthesizes `text` with `voice_id` and returns `audio/wav` |

`POST /generate` body:

```json
{ "text": "Vocês ouvem passos no corredor.", "voice_id": "pt-br-kokoro-santa" }
```

- `text`: 1 to 5000 characters, required.
- `voice_id`: optional. If it is missing, `TTS_DEFAULT_VOICE_ID` is used.
- Errors: `404` for an unknown voice, `422` for an invalid body, `500` when the engine fails (the error message is in `detail`).

### curl examples

```bash
# health
curl -s http://127.0.0.1:8002/health
# {"status":"ok","service":"Lunaria Open TTS","voices":7}

# list voices
curl -s http://127.0.0.1:8002/voices
# {"success":true,"data":[{"voice_id":"pt-br-faber-medium","name":"Faber PT-BR","language":"pt-BR","provider":"piper"}, ...]}

# synthesize with Kokoro
curl -s -X POST http://127.0.0.1:8002/generate \
  -H 'Content-Type: application/json' \
  -d '{"text":"O dragão acordou na caverna.","voice_id":"pt-br-kokoro-santa"}' \
  -o dragao.wav

# synthesize with Piper
curl -s -X POST http://127.0.0.1:8002/generate \
  -H 'Content-Type: application/json' \
  -d '{"text":"Role os dados, aventureiro corajoso.","voice_id":"pt-br-faber-medium"}' \
  -o dados.wav
```

## Running it

### Without Docker

Requirements: Python 3.10+ (production runs 3.10.12 and CI uses 3.11), plus a Piper binary if you want Piper voices.

```bash
git clone https://github.com/mazocelo/lunaria-open-tts.git
cd lunaria-open-tts
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt     # pulls kokoro + torch (CPU)
cp .env.example .env                          # then edit it (see below)
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8002
```

On Windows, `scripts/start.ps1` starts uvicorn with `--reload`.

**Piper voices.** Download a Piper release binary from [rhasspy/piper](https://github.com/rhasspy/piper/releases). Then download each voice's `.onnx` and `.onnx.json` files from [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_BR).

**Kokoro voices.** No manual download. The weights (`hexgrad/Kokoro-82M`, about 330 MB with three voices) are fetched into the Hugging Face cache on the first Kokoro request.

Example `.env`:

```env
TTS_SERVICE_NAME=Lunaria Open TTS
TTS_HOST=127.0.0.1
TTS_PORT=8002
PIPER_EXECUTABLE=/opt/piper-runtime/piper/piper
TTS_DEFAULT_VOICE_ID=pt-br-faber-medium
PIPER_OUTPUT_SAMPLE_RATE=22050
PIPER_VOICES_JSON=[{"voice_id":"pt-br-faber-medium","name":"Faber PT-BR","language":"pt-BR","backend":"piper","model_path":"/opt/piper/voices/pt_BR/faber/medium/pt_BR-faber-medium.onnx","config_path":"/opt/piper/voices/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json"},{"voice_id":"pt-br-kokoro-santa","name":"Santa PT-BR","language":"pt-BR","backend":"kokoro","kokoro_voice":"pm_santa"}]
```

Note that `TTS_HOST` and `TTS_PORT` are not read by uvicorn. Pass `--host` and `--port` on the command line.

### As a systemd service (how production runs it)

```ini
[Unit]
Description=Lunaria Open TTS
After=network.target

[Service]
WorkingDirectory=/opt/lunaria-open-tts
EnvironmentFile=/opt/lunaria-open-tts/.env
ExecStart=/opt/lunaria-open-tts/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8002
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### With Docker

There is no Dockerfile yet. The service only needs Python, the pip requirements, the Piper binary and the voice files, so it is straightforward to containerize. It is just not provided.

### CI/CD

`.github/workflows/ci-cd.yml` runs `ruff check app/` and an import check on every push and pull request. On a push to `main`, it deploys over SSH: `git pull --ff-only`, `pip install`, `systemctl restart lunaria-open-tts`.

## Benchmark

Measured on 2026-11-02 against the production instance, on CPU only.

- **Hardware:** VPS with 4 vCPU AMD EPYC 9J45 (KVM, 1 thread per core) and 7.7 GiB RAM. **No GPU** (only a virtio display adapter).
- **Software:** Python 3.10.12, torch 2.10.0 (CPU), kokoro 0.9.4.
- **Method:** 10 Portuguese sentences, sent to `POST /generate` one at a time with a 1-second pause between requests. There were 4 sentences of 5 words, 3 of 15 words and 3 of 40 words. Each sentence ran twice per voice, which gives n = 20 per voice.
- **What was measured:** total latency is measured on the client from request to last byte. Audio duration comes from the WAV header. RTF (real-time factor) is synthesis time ÷ audio duration, so lower is better and below 1 is faster than real time.
- **Excluded:** one warm-up request per voice. The first Kokoro request took 8.2 s and the first Piper request took 0.55 s. All 40 measured requests returned HTTP 200.

| Voice | Engine | Latency p50 | Latency p95 | RTF p50 | RTF p95 | RTF overall* | p50, 5 words | p50, 15 words | p50, 40 words |
|---|---|---|---|---|---|---|---|---|---|
| `pt-br-kokoro-santa` | Kokoro-82M | 1.07 s | 4.61 s | 0.19 | 2.01 | 0.30 | 0.63 s (2.4 s audio) | 0.93 s (5.4 s audio) | 2.28 s (12.8 s audio) |
| `pt-br-faber-medium` | Piper | 0.38 s | 1.18 s | 0.10 | 0.20 | 0.09 | 0.30 s (1.9 s audio) | 0.38 s (4.9 s audio) | 0.88 s (11.7 s audio) |

\* RTF overall is the sum of synthesis time divided by the sum of audio duration.

Notes:

- **Time to first byte equals total latency.** The endpoint does not stream, so the WAV is sent only after it has been fully synthesized.
- **The Kokoro p95 comes from two outliers.** Two short sentences took 4.3 s and 10.7 s. Both happened right after switching back from Piper. When this ran, the long-running service process had about 400 MB in swap, and paging the model back in is the likely cause. That cause is not proven. The other 18 Kokoro requests stayed between 0.41 s and 2.65 s, with RTF between 0.15 and 0.48.
- Excluding those two outliers, Kokoro produces speech about 5 to 6 times faster than real time on 15- and 40-word sentences. Piper is about 10 to 20 times faster than real time, even though it starts a new process for every request.

## Used in production by Lunaria

Lunaria is a web tabletop RPG where an LLM game master narrates the scenes. Its Node.js backend uses this service as the **default TTS provider**:

```env
DEFAULT_TTS_PROVIDER=opensource
OPEN_SOURCE_TTS_URL=http://127.0.0.1:8002
OPEN_SOURCE_TTS_DEFAULT_VOICE_ID=pt-br-kokoro-santa
```

- The backend sends the narration text to `POST /generate` and receives a WAV. It caches the audio on its side, keyed by text and voice, so a repeated line is not synthesized twice. It also reads `GET /voices` so a voice can be assigned to each character.
- Both services run on the same VPS. The TTS listens only on `127.0.0.1`, is managed by systemd and is not exposed to the internet.
- Paid cloud TTS providers remain available in Lunaria as alternatives. This service is the default because it costs nothing per character.

## Limitations

- No streaming and no chunked responses.
- No authentication. Keep it on localhost or behind a reverse proxy that handles auth.
- Piper starts a new process and loads its model on every request.
- The endpoint is synchronous, so concurrency is limited by uvicorn's threadpool and the CPU.
- There is no automated test suite yet. CI only runs lint and an import check.

## License

The **code** in this repository is released under the [MIT License](LICENSE). Copyright (c) 2026 Marcelo Mazarem.

## Voice model licenses

**The MIT license covers the code only.** This repository does not include any model weights or voice files. You download them from their upstream sources, and they keep their own licenses.

No model card or license file is stored next to the models on the production server. The information below comes from the upstream model cards (checked 2026-11-02). The SHA-256 prefixes of the three Kokoro voice files in the local cache match the ones published in Kokoro's `VOICES.md`. **Check these licenses yourself before any commercial use.**

| `voice_id` | Model | Training data (per the model card) | License |
|---|---|---|---|
| `pt-br-kokoro-santa`, `pt-br-kokoro-alex`, `pt-br-kokoro-dora` | [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) v1.0, voices `pm_santa`, `pm_alex`, `pf_dora` | Permissive or non-copyrighted audio, per the model card | **Apache-2.0** (model weights) |
| `pt-br-faber-medium` | [piper-voices pt_BR faber medium](https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_BR/faber/medium) | [OHF-Voice/voice-datasets](https://github.com/OHF-Voice/voice-datasets), **CC0** | Dataset CC0. Fine-tuned from `en_US-lessac-medium`, whose dataset (Blizzard 2013 Lessac) is **research-only and non-commercial**, so commercial use is unclear |
| `pt-br-cadu-medium` | [piper-voices pt_BR cadu medium](https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_BR/cadu/medium) | OHF-Voice/voice-datasets, **CC0** | Same as faber: fine-tuned from `lessac-medium`, so commercial use is unclear |
| `pt-br-jeff-medium` | [piper-voices pt_BR jeff medium](https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_BR/jeff/medium) | OHF-Voice/voice-datasets, **CC0** | Same as faber: fine-tuned from `lessac-medium`, so commercial use is unclear |
| `pt-br-edresson-low` | [piper-voices pt_BR edresson low](https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_BR/edresson/low) | [TTS-Portuguese-Corpus](https://github.com/Edresson/TTS-Portuguese-Corpus), **CC BY 4.0** (attribution required) | Fine-tuned from `en_US-ryan-low`, whose dataset (RyanSpeech) is **CC BY-NC-SA 4.0**. Treat as non-commercial |

In practice:

- The **Kokoro voices** have the clearest license (Apache-2.0).
- For the **Piper pt_BR voices**, the voice's own dataset is permissive, but the checkpoint each one was fine-tuned from comes from a non-commercial dataset. Treat them as non-commercial unless you get confirmation otherwise.

**Third-party runtimes** are installed separately and are not distributed here:

- The Piper release binary bundles `libespeak-ng` (GPL-3.0).
- Kokoro uses `misaki` (Apache-2.0) and `espeak-ng` (through `espeakng-loader`) for Portuguese phonemes.
- `torch` is BSD-3-Clause, FastAPI is MIT and `soundfile` is BSD-3-Clause.
