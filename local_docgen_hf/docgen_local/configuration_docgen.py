from transformers import PretrainedConfig


class DocGenConfig(PretrainedConfig):
    model_type = "docgen-local"

    def __init__(
        self,
        vocab_size: int = 32000,
        hidden_size: int = 256,
        num_layers: int = 2,
        dropout: float = 0.1,
        pad_token_id: int = 0,
        bos_token_id: int = 1,
        eos_token_id: int = 2,
        **kwargs,
    ):
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        super().__init__(
            pad_token_id=pad_token_id,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
            **kwargs,
        )
