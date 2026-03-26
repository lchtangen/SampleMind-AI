# Remote Inference for Low-Memory Systems

If you cannot load a model locally (e.g., running on WSL2 with 8 GB RAM), use a remote
inference API or a local server such as Ollama.

> **SampleMind Phase 12 uses LiteLLM** — the examples below use both the native APIs and
> LiteLLM's unified interface. LiteLLM is the recommended pattern for new code.

---

## 1. LiteLLM — Provider-Agnostic (Recommended)

LiteLLM provides a single `completion()` call that works with Anthropic, OpenAI, Ollama,
and 100+ other providers. Phase 12 (AI Curation Agent) uses this pattern.

```python
import litellm

# Anthropic Claude
response = litellm.completion(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "Analyze this sample library gap"}],
)

# OpenAI GPT-4o (same interface, different model string)
response = litellm.completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Analyze this sample library gap"}],
)

# Local Ollama (no API key needed)
response = litellm.completion(
    model="ollama/llama3",
    messages=[{"role": "user", "content": "Analyze this sample library gap"}],
)

print(response.choices[0].message.content)
```

Install: `uv add litellm`

---

## 2. Hugging Face Inference API

```python
from huggingface_hub import InferenceClient

client = InferenceClient(token="hf_...")
result = client.text_generation(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    prompt="Generate a description for a dark trap kick sample",
    max_new_tokens=200,
)
print(result)
```

Install: `uv add huggingface-hub`

---

## 3. Ollama (Local LLM Server)

Ollama runs models locally with a REST API — no API key, no internet required.

```bash
# Install and start (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh
ollama serve

# Pull a model (one-time download)
ollama pull llama3
ollama pull mistral
```

```python
import requests

response = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "llama3",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False,
    },
)
print(response.json()["message"]["content"])
```

Or use LiteLLM's Ollama integration (section 1 above) for a consistent interface.

---

## 4. OpenAI API (openai >= 1.0)

```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")  # or set OPENAI_API_KEY env var

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)
```

Install: `uv add openai`

> **Note:** The legacy `openai.ChatCompletion.create()` module-level API was removed in
> `openai>=1.0.0` (November 2023). Always use the client instance pattern above.

---

## 5. Choosing a Smaller Model

When memory is the constraint (< 8 GB VRAM / < 16 GB RAM):

| Model | Size | Notes |
|-------|------|-------|
| `llama3.2:1b` | ~1 GB | Good for short classification tasks |
| `mistral:7b-instruct-q4` | ~4 GB | 4-bit quantized, good quality |
| `phi3:mini` | ~2 GB | Microsoft Phi-3, fast and capable |
| `gemma2:2b` | ~1.5 GB | Google Gemma 2B |

See [quantization_and_offloading.md](quantization_and_offloading.md) for loading larger
models with bitsandbytes 4-bit or 8-bit quantization.

---

## Environment Variables

```bash
# Set in .env (never commit) or export in shell:
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
HUGGINGFACE_TOKEN=hf_...

# LiteLLM reads these automatically — no manual passing required
```
