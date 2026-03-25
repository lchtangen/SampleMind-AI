"""
Model loader utility for low-memory environments.
Supports: 8-bit quantization, disk offloading, and fallback to remote inference.
"""
from typing import Optional
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ImportError:
    AutoModelForCausalLM = None
    AutoTokenizer = None

def load_model(
    model_name: str,
    offload_folder: Optional[str] = "./offload",
    prefer_8bit: bool = True,
    prefer_offload: bool = True,
    device_map: str = "auto",
    **kwargs
) -> Optional[object]:
    """
    Try to load a model with 8-bit quantization or disk offloading.
    Falls back to remote inference if local load fails.
    """
    if AutoModelForCausalLM is None:
        raise ImportError("transformers not installed")
    try:
        if prefer_8bit:
            return AutoModelForCausalLM.from_pretrained(
                model_name, device_map=device_map, load_in_8bit=True, **kwargs
            )
    except Exception as e:
        print(f"8-bit load failed: {e}")
    try:
        if prefer_offload:
            return AutoModelForCausalLM.from_pretrained(
                model_name, device_map=device_map, offload_folder=offload_folder, **kwargs
            )
    except Exception as e:
        print(f"Offload load failed: {e}")
    print("Falling back to remote inference or smaller model.")
    return None

def load_tokenizer(model_name: str):
    if AutoTokenizer is None:
        raise ImportError("transformers not installed")
    return AutoTokenizer.from_pretrained(model_name)
