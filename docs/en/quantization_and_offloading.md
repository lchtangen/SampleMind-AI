# Model quantization and offloading — quick guide

When a local model fails to load with "model requires more system memory" errors, use one or more of these approaches:

1) Add swap (temporary)

```
# Linux (adds 4GiB swap)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
free -h
```

2) Load the model in 8-bit (requires `bitsandbytes` + compatible CUDA runtime)

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("model-name")
model = AutoModelForCausalLM.from_pretrained(
    "model-name",
    device_map="auto",
    load_in_8bit=True,
)

# then use model.generate(...)
```

3) Use `accelerate` offloading to stream weights from disk/CPU

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from accelerate import init_empty_weights, load_checkpoint_and_dispatch

# Option A — simple (device_map auto + offload_folder)
model = AutoModelForCausalLM.from_pretrained(
    "model-name",
    device_map="auto",
    offload_folder="./offload",
)

# Option B — advanced accelerate utilities
```

4) Use a smaller model or remote inference (API or local server)

Notes
- If you rely on `uv` for dependency management, add packages with `uv add bitsandbytes accelerate` (or your chosen manager).
- `load_in_8bit=True` requires `bitsandbytes` and a supported CUDA environment; it will not help on pure-CPU machines.
- Offloading to disk reduces RAM requirements but is slower — good for CI or development.

If you want, I can add a small helper loader utility to `src/` that wraps these options and falls back automatically. Tell me where you'd like it placed.
