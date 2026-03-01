import torch
from torch import nn
from transformers import PreTrainedModel
from transformers.generation import GenerationMixin
from transformers.modeling_outputs import CausalLMOutput

from .configuration_docgen import DocGenConfig


class DocGenForCausalLM(PreTrainedModel, GenerationMixin):
    config_class = DocGenConfig
    base_model_prefix = "docgen"
    main_input_name = "input_ids"

    def __init__(self, config: DocGenConfig):
        super().__init__(config)
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        self.rnn = nn.GRU(
            input_size=config.hidden_size,
            hidden_size=config.hidden_size,
            num_layers=config.num_layers,
            dropout=config.dropout if config.num_layers > 1 else 0.0,
            batch_first=True,
        )
        self.dropout = nn.Dropout(config.dropout)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

        self.post_init()

    def get_input_embeddings(self):
        return self.embed_tokens

    def set_input_embeddings(self, value):
        self.embed_tokens = value

    def forward(self, input_ids=None, attention_mask=None, labels=None, **kwargs):
        if input_ids is None:
            raise ValueError("input_ids must be provided")

        embeddings = self.embed_tokens(input_ids)
        hidden_states, _ = self.rnn(embeddings)
        hidden_states = self.dropout(hidden_states)
        logits = self.lm_head(hidden_states)

        loss = None
        if labels is not None:
            shift_logits = logits[:, :-1, :].contiguous()
            shift_labels = labels[:, 1:].contiguous()
            loss_fct = nn.CrossEntropyLoss(ignore_index=-100)
            loss = loss_fct(
                shift_logits.view(-1, self.config.vocab_size),
                shift_labels.view(-1),
            )

        return CausalLMOutput(loss=loss, logits=logits)

    def prepare_inputs_for_generation(self, input_ids, attention_mask=None, **kwargs):
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }


DocGenConfig.register_for_auto_class()
DocGenForCausalLM.register_for_auto_class("AutoModelForCausalLM")