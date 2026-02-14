"""Central configuration for Llama 3.1 8B legal fine-tuning."""

from pathlib import Path

# ======================================================================
# Document source directories
# ======================================================================

DOCUMENT_DIRS = [
    Path(r"C:\Users\SJK\Documents"),
    Path(r"C:\Users\SJK\Cypress LLP"),
    Path(r"C:\Users\SJK\OneDrive - Cypress LLP"),
]

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# ======================================================================
# Quality filters
# ======================================================================

MIN_TEXT_LENGTH = 200        # Skip docs with fewer chars
MAX_NON_ASCII_RATIO = 0.50   # Skip docs with >50% non-ASCII

# ======================================================================
# Model & LoRA settings
# ======================================================================

BASE_MODEL = "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"
MAX_SEQ_LENGTH = 2048

LORA_RANK = 16
LORA_ALPHA = 16
LORA_DROPOUT = 0
LORA_TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]

# Fallback settings if OOM occurs (triggered by --fallback flag)
FALLBACK_LORA_RANK = 8
FALLBACK_MAX_SEQ_LENGTH = 1024

# ======================================================================
# Training hyperparameters
# ======================================================================

PER_DEVICE_BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 8
NUM_EPOCHS = 1
LEARNING_RATE = 2e-4
WARMUP_STEPS = 10
WEIGHT_DECAY = 0.01
OPTIMIZER = "adamw_8bit"
LR_SCHEDULER = "linear"
LOGGING_STEPS = 10
SAVE_STEPS = 200
SEED = 42

# ======================================================================
# Chunking
# ======================================================================

MAX_DOC_CHARS = 7000         # Docs longer than this get chunked
CHUNK_SIZE = 6000            # Target chunk size in characters
CHUNK_OVERLAP = 500          # Overlap between chunks

# ======================================================================
# Output paths (relative to project root)
# ======================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FINETUNE_DIR = PROJECT_ROOT / "finetune"
OUTPUT_DIR = PROJECT_ROOT / "finetune_output"

TRAINING_DATA_DIR = OUTPUT_DIR / "training_data"
TRAINING_DATA_FILE = TRAINING_DATA_DIR / "legal_style_training.jsonl"

LORA_OUTPUT_DIR = OUTPUT_DIR / "lora_adapter"
GGUF_OUTPUT_DIR = OUTPUT_DIR / "gguf"
GGUF_FILE = GGUF_OUTPUT_DIR / "llama3.1-legal-q4_k_m.gguf"
MODELFILE_PATH = GGUF_OUTPUT_DIR / "Modelfile"

OLLAMA_MODEL_NAME = "llama3.1-legal:8b"

# ======================================================================
# System prompt used in training examples
# ======================================================================

TRAINING_SYSTEM_PROMPT = (
    "You are a professional legal document drafting assistant at a corporate law firm. "
    "Draft documents using precise legal language, proper formatting with numbered sections, "
    "and a professional tone consistent with high-quality legal practice. "
    "Do NOT provide legal advice — produce drafts for attorney review."
)
