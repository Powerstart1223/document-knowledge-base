# Local Hugging Face Integration Starter (Document Generator)

This starter gives you a local-only path for wrapping an existing document generator with Hugging Face `transformers` APIs.

## Files

- `docgen_local/configuration_docgen.py`: `PretrainedConfig` implementation.
- `docgen_local/modeling_docgen.py`: `PreTrainedModel` CausalLM wrapper.
- `integrate_existing_model.py`: bridge for the existing project pipeline (`hf` or `ollama`).
- `run_local_demo.py`: saves, reloads, and runs local token generation.
- `requirements.txt`: minimal dependencies.

## 1) Install dependencies

```powershell
cd C:\Users\SJK\document-knowledge-base\local_docgen_hf
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If `venv` cannot bootstrap pip in your environment, use global pip:

```powershell
python -m pip install -r requirements.txt
```

## 2) Run local demo

```powershell
python run_local_demo.py
```

This writes a local model folder `./local_saved_docgen` containing:

- `config.json`
- `model.safetensors`
- `modeling_docgen.py` (for local class loading)

## 3) Bridge your existing project generator

Your production generator is prompt-based (`DocumentGenerator` + `LLMBackend`).
Use this bridge to keep that pipeline and choose backend at runtime.

### Ollama mode (recommended for your current setup)

```powershell
python integrate_existing_model.py --provider ollama --ollama-model llama3.1:8b --document-type employment_agreement
```

### Hugging Face local-folder mode

```powershell
python integrate_existing_model.py --provider hf --model-path C:\path\to\your\local\hf-model --document-type employment_agreement --top-k 50 --top-p 0.95
```

HF `--model-path` must contain model + tokenizer artifacts (`config.json`, weights, tokenizer files).

HF sampling uses sequential filters in this order: `temperature -> top-k -> top-p`.

## 4) Notes

- `C:\Users\SJK\.ollama` is not a Hugging Face model folder and cannot be used as `--model-path`.
- Keep using Ollama mode unless you export/download a real local HF causal LM directory.
