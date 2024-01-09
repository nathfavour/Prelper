from typing import Any, Dict

from transformers import GenerationConfig

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings


class HuggingFaceRequestSettings(AIRequestSettings):
    do_sample: bool = True
    max_new_tokens: int = 256
    num_return_sequences: int = 1
    stop_sequences: Any = None
    pad_token_id: int = 50256
    temperature: float = 0.0
    top_p: float = 1.0

    def get_generation_config(self) -> GenerationConfig:
        return GenerationConfig(
            **self.model_dump(
                include={"max_new_tokens", "pad_token_id", "temperature", "top_p"},
                exclude_unset=True,
                exclude_none=True,
                by_alias=True,
            )
        )

    def prepare_settings_dict(self, **kwargs) -> Dict[str, Any]:
        gen_config = self.get_generation_config()
        if "prompt" in kwargs and kwargs["prompt"] is not None:
            return {
                "text_inputs": kwargs["prompt"],
                "generation_config": gen_config,
                "num_return_sequences": self.num_return_sequences,
                "do_sample": self.do_sample,
            }
        return {
            "generation_config": gen_config,
            "num_return_sequences": self.num_return_sequences,
            "do_sample": self.do_sample,
        }
