import torch

from docgen_local import DocGenConfig, DocGenForCausalLM


def main():
    model_dir = "./local_saved_docgen"

    config = DocGenConfig(
        vocab_size=5000,
        hidden_size=192,
        num_layers=2,
        dropout=0.1,
        bos_token_id=1,
        eos_token_id=2,
        pad_token_id=0,
    )
    model = DocGenForCausalLM(config)
    model.save_pretrained(model_dir, safe_serialization=True)

    loaded = DocGenForCausalLM.from_pretrained(model_dir)
    loaded.eval()

    input_ids = torch.tensor([[1, 45, 712, 88]], dtype=torch.long)
    with torch.no_grad():
        generated = loaded.generate(
            input_ids=input_ids,
            max_new_tokens=24,
            do_sample=True,
            top_p=0.95,
            temperature=0.9,
            eos_token_id=config.eos_token_id,
            pad_token_id=config.pad_token_id,
        )

    print("Input token ids:", input_ids.tolist())
    print("Generated token ids:", generated.tolist())


if __name__ == "__main__":
    main()