# Lunaria Open TTS

Servico de TTS local para a Lunaria usando modelo open source via Piper.

## Stack

- Python 3.11+
- FastAPI
- Uvicorn
- Piper CLI

## Endpoints

- `GET /health`
- `GET /voices`
- `POST /generate`

## Setup

1. Instale o `piper` na maquina.
2. Baixe uma voz PT-BR compatível com Piper.
3. Copie `.env.example` para `.env`.
4. Ajuste `PIPER_VOICES_JSON` com os caminhos reais do modelo.
5. Instale as dependencias:

```bash
pip install -r requirements.txt
```

6. Rode o servidor:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## Voz recomendada para RPG

Recomendacao inicial:

- `pt_BR-faber-medium`

Exemplo de configuracao:

```env
TTS_DEFAULT_VOICE_ID=pt-br-faber-medium
PIPER_VOICES_JSON=[{"voice_id":"pt-br-faber-medium","name":"Faber PT-BR","language":"pt-BR","model_path":"C:/tts-models/pt_BR-faber-medium.onnx","config_path":"C:/tts-models/pt_BR-faber-medium.onnx.json"}]
```

## Integracao com o backend principal

Use estas variaveis no backend que vai consumir este servico:

```env
DEFAULT_TTS_PROVIDER=opensource
OPEN_SOURCE_TTS_URL=http://localhost:8002
OPEN_SOURCE_TTS_DEFAULT_VOICE_ID=pt-br-faber-medium
```
