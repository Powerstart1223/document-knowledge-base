"""Export fine-tuned model to GGUF and register with Ollama.

Usage:
    python export_to_ollama.py
"""

import argparse
import subprocess
import sys

from config import (
    BASE_MODEL,
    GGUF_FILE,
    GGUF_OUTPUT_DIR,
    LORA_OUTPUT_DIR,
    MAX_SEQ_LENGTH,
    MODELFILE_PATH,
    OLLAMA_MODEL_NAME,
    TRAINING_SYSTEM_PROMPT,
)


# ======================================================================
# Ollama Modelfile content
# ======================================================================

MODELFILE_TEMPLATE = '''FROM {gguf_path}

TEMPLATE """{{{{- if .System }}}}<|start_header_id|>system<|end_header_id|>

{{{{ .System }}}}<|eot_id|>{{{{- end }}}}
<|start_header_id|>user<|end_header_id|>

{{{{ .Prompt }}}}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>

{{{{ .Response }}}}<|eot_id|>"""

PARAMETER stop "<|start_header_id|>"
PARAMETER stop "<|end_header_id|>"
PARAMETER stop "<|eot_id|>"
PARAMETER num_ctx {num_ctx}

SYSTEM """{system_prompt}"""
'''


def main():
    parser = argparse.ArgumentParser(description="Export a trained adapter to Ollama model")
    parser.add_argument("--model-name", default=OLLAMA_MODEL_NAME)
    args = parser.parse_args()
    model_name = args.model_name

    # ------------------------------------------------------------------
    # 1. Verify LoRA adapter exists
    # ------------------------------------------------------------------
    if not LORA_OUTPUT_DIR.exists():
        print(f"ERROR: LoRA adapter not found at {LORA_OUTPUT_DIR}")
        print("Run train.py first.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Export to GGUF
    # ------------------------------------------------------------------
    print("=" * 60)
    print("EXPORTING MODEL TO GGUF")
    print("=" * 60)

    GGUF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1/4] Loading model + LoRA adapter and exporting to GGUF...")
    print("  This may take 5-10 minutes and use significant RAM.")

    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(LORA_OUTPUT_DIR),
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=True,
    )

    model.save_pretrained_gguf(
        str(GGUF_OUTPUT_DIR),
        tokenizer,
        quantization_method="q4_k_m",
    )

    # Find the actual GGUF file (Unsloth names it automatically)
    gguf_files = list(GGUF_OUTPUT_DIR.glob("*.gguf"))
    if not gguf_files:
        print("ERROR: No GGUF file was produced. Check Unsloth output above.")
        sys.exit(1)

    actual_gguf = gguf_files[0]
    print(f"  GGUF exported: {actual_gguf} ({actual_gguf.stat().st_size / 1024**3:.2f} GB)")

    # ------------------------------------------------------------------
    # 3. Generate Modelfile
    # ------------------------------------------------------------------
    print("\n[2/4] Generating Ollama Modelfile...")

    modelfile_content = MODELFILE_TEMPLATE.format(
        gguf_path=str(actual_gguf).replace("\\", "/"),
        num_ctx=MAX_SEQ_LENGTH,
        system_prompt=TRAINING_SYSTEM_PROMPT,
    )
    MODELFILE_PATH.write_text(modelfile_content, encoding="utf-8")
    print(f"  Modelfile written to: {MODELFILE_PATH}")

    # ------------------------------------------------------------------
    # 4. Register with Ollama
    # ------------------------------------------------------------------
    print(f"\n[3/4] Creating Ollama model '{model_name}'...")

    result = subprocess.run(
        ["ollama", "create", model_name, "-f", str(MODELFILE_PATH)],
        capture_output=True, text=True, timeout=300,
    )

    if result.returncode != 0:
        print(f"  ERROR: ollama create failed:\n{result.stderr}")
        sys.exit(1)

    print(f"  {result.stdout.strip()}")

    # Verify it shows up
    result = subprocess.run(
        ["ollama", "list"], capture_output=True, text=True, timeout=30,
    )
    if model_name.split(":")[0] in result.stdout:
        print(f"  Verified: '{model_name}' appears in ollama list")
    else:
        print(f"  WARNING: '{model_name}' not found in ollama list")
        print(f"  Output: {result.stdout}")

    # ------------------------------------------------------------------
    # 5. Smoke test
    # ------------------------------------------------------------------
    print("\n[4/4] Running smoke test...")

    test_prompts = [
        "Draft an indemnification clause for a service agreement.",
        "Write a brief introduction for a motion to dismiss.",
        "Draft a confidentiality provision for a settlement agreement.",
    ]

    for prompt in test_prompts:
        print(f"\n  Prompt: {prompt}")
        print("  " + "-" * 50)

        try:
            result = subprocess.run(
                ["ollama", "run", model_name, prompt],
                capture_output=True, text=True, timeout=120,
            )
            # Show first 300 chars of response
            response = result.stdout.strip()[:300]
            print(f"  Response: {response}...")
        except subprocess.TimeoutExpired:
            print("  [Timed out after 120s — model may still be loading]")
        except Exception as e:
            print(f"  [Error: {e}]")

    print("\n" + "=" * 60)
    print("EXPORT COMPLETE")
    print("=" * 60)
    print(f"  Model registered as: {model_name}")
    print("  The model will appear in the Streamlit app Settings dropdown.")


if __name__ == "__main__":
    main()
