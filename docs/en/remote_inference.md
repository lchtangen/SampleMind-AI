# Remote inference for low-memory systems

If you cannot load a model locally, use a remote inference API or local server:

## 1. Hugging Face Inference API

```python
from huggingface_hub import InferenceClient
client = InferenceClient(token="your-hf-token")
result = client.text_generation("gpt2", "Hello world")
```

## 2. Ollama (local LLM server)

Start Ollama server:
```
ollama serve
ollama run llama2
```
Python:
```python
import requests
resp = requests.post("http://localhost:11434/api/generate", json={"model": "llama2", "prompt": "Hello"})
print(resp.json())
```

## 3. OpenAI API

```python
import openai
openai.api_key = "sk-..."
resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello"}])
print(resp.choices[0].message.content)
```

## 4. Use a smaller model

Choose a model with fewer parameters (e.g., distilGPT2, TinyLlama, etc.)

---
See also: [quantization_and_offloading.md](quantization_and_offloading.md)
