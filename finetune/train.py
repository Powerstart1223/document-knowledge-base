"""QLoRA fine-tuning of Llama 3.1 8B on legal documents using Unsloth.

Usage:
    python train.py              # Normal training
    python train.py --fallback   # Reduced settings if OOM occurs
"""

import argparse
import sys
from pathlib import Path

from config import (
    BASE_MODEL,
    FALLBACK_LORA_RANK,
    FALLBACK_MAX_SEQ_LENGTH,
    GRADIENT_ACCUMULATION_STEPS,
    LEARNING_RATE,
    LOGGING_STEPS,
    LORA_ALPHA,
    LORA_DROPOUT,
    LORA_RANK,
    LORA_TARGET_MODULES,
    LR_SCHEDULER,
    MAX_SEQ_LENGTH,
    NUM_EPOCHS,
    OPTIMIZER,
    OUTPUT_DIR,
    PER_DEVICE_BATCH_SIZE,
    SAVE_STEPS,
    SEED,
    TRAINING_DATA_FILE,
    LORA_OUTPUT_DIR,
    WARMUP_STEPS,
    WEIGHT_DECAY,
)


def main():
    parser = argparse.ArgumentParser(description="Fine-tune Llama 3.1 8B on legal docs")
    parser.add_argument(
        "--fallback", action="store_true",
        help="Use reduced settings (r=8, seq_len=1024) to avoid OOM",
    )
    args = parser.parse_args()

    # Resolve settings
    lora_rank = FALLBACK_LORA_RANK if args.fallback else LORA_RANK
    max_seq_len = FALLBACK_MAX_SEQ_LENGTH if args.fallback else MAX_SEQ_LENGTH

    if args.fallback:
        print("[INFO] Using fallback settings: r=8, max_seq_length=1024")

    # ------------------------------------------------------------------
    # Verify training data exists
    # ------------------------------------------------------------------
    if not TRAINING_DATA_FILE.exists():
        print(f"ERROR: Training data not found at {TRAINING_DATA_FILE}")
        print("Run prepare_data.py first.")
        sys.exit(1)

    line_count = sum(1 for _ in open(TRAINING_DATA_FILE, encoding="utf-8"))
    print(f"Training data: {line_count} examples from {TRAINING_DATA_FILE}")

    # ------------------------------------------------------------------
    # Load model with Unsloth (4-bit quantized)
    # ------------------------------------------------------------------
    print("\n[1/4] Loading model...")
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=max_seq_len,
        dtype=None,  # Auto-detect
        load_in_4bit=True,
    )

    # ------------------------------------------------------------------
    # Apply LoRA adapters
    # ------------------------------------------------------------------
    print("\n[2/4] Applying LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_rank,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES,
        bias="none",
        use_gradient_checkpointing="unsloth",  # Smart offload to RAM
        random_state=SEED,
    )

    # Print trainable parameter count
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"  Trainable parameters: {trainable:,} / {total:,} ({100 * trainable / total:.2f}%)")

    # ------------------------------------------------------------------
    # Load and format dataset
    # ------------------------------------------------------------------
    print("\n[3/4] Loading and formatting dataset...")
    from datasets import load_dataset
    from unsloth.chat_templates import get_chat_template, standardize_sharegpt

    tokenizer = get_chat_template(tokenizer, chat_template="llama-3.1")

    dataset = load_dataset("json", data_files=str(TRAINING_DATA_FILE), split="train")
    dataset = standardize_sharegpt(dataset)

    def apply_template(examples):
        texts = [
            tokenizer.apply_chat_template(
                convo, tokenize=False, add_generation_prompt=False,
            )
            for convo in examples["conversations"]
        ]
        return {"text": texts}

    dataset = dataset.map(apply_template, batched=True)
    print(f"  Dataset size: {len(dataset)} examples")

    # ------------------------------------------------------------------
    # Train
    # ------------------------------------------------------------------
    print("\n[4/4] Starting training...")
    from trl import SFTTrainer
    from transformers import TrainingArguments

    checkpoint_dir = OUTPUT_DIR / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_len,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            output_dir=str(checkpoint_dir),
            per_device_train_batch_size=PER_DEVICE_BATCH_SIZE,
            gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
            num_train_epochs=NUM_EPOCHS,
            learning_rate=LEARNING_RATE,
            warmup_steps=WARMUP_STEPS,
            weight_decay=WEIGHT_DECAY,
            optim=OPTIMIZER,
            lr_scheduler_type=LR_SCHEDULER,
            logging_steps=LOGGING_STEPS,
            save_steps=SAVE_STEPS,
            save_total_limit=2,
            fp16=True,
            seed=SEED,
            report_to="none",
        ),
    )

    gpu_stats = None
    try:
        import torch
        if torch.cuda.is_available():
            gpu_stats = torch.cuda.get_device_properties(0)
            print(f"  GPU: {gpu_stats.name} ({gpu_stats.total_mem / 1024**3:.1f} GB)")
    except Exception:
        pass

    train_result = trainer.train()

    # Print results
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Training loss: {train_result.training_loss:.4f}")
    print(f"  Training steps: {train_result.global_step}")
    print(f"  Training samples: {train_result.metrics.get('train_samples', 'N/A')}")

    # ------------------------------------------------------------------
    # Save LoRA adapter
    # ------------------------------------------------------------------
    LORA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(LORA_OUTPUT_DIR))
    tokenizer.save_pretrained(str(LORA_OUTPUT_DIR))
    print(f"\n  LoRA adapter saved to: {LORA_OUTPUT_DIR}")


if __name__ == "__main__":
    main()
