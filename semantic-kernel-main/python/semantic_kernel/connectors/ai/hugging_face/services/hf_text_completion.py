# Copyright (c) Microsoft. All rights reserved.

import logging
from threading import Thread
from typing import Any, Dict, List, Literal, Optional, Union

import torch
import transformers

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.hugging_face.hf_request_settings import (
    HuggingFaceRequestSettings,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)

logger: logging.Logger = logging.getLogger(__name__)


class HuggingFaceTextCompletion(TextCompletionClientBase, AIServiceClientBase):
    task: Literal["summarization", "text-generation", "text2text-generation"]
    device: str
    generator: Any

    def __init__(
        self,
        ai_model_id: str,
        task: Optional[str] = "text2text-generation",
        device: Optional[int] = -1,
        log: Optional[Any] = None,
        model_kwargs: Optional[Dict[str, Any]] = None,
        pipeline_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initializes a new instance of the HuggingFaceTextCompletion class.

        Arguments:
            ai_model_id {str} -- Hugging Face model card string, see
                https://huggingface.co/models
            device {Optional[int]} -- Device to run the model on, defaults to CPU, 0+ for GPU,
                                   -- None if using device_map instead. (If both device and device_map
                                      are specified, device overrides device_map. If unintended,
                                      it can lead to unexpected behavior.)
            task {Optional[str]} -- Model completion task type, options are:
                - summarization: takes a long text and returns a shorter summary.
                - text-generation: takes incomplete text and returns a set of completion candidates.
                - text2text-generation (default): takes an input prompt and returns a completion.
                text2text-generation is the default as it behaves more like GPT-3+.
            log  -- Logger instance. (Deprecated)
            model_kwargs {Optional[Dict[str, Any]]} -- Additional dictionary of keyword arguments
                passed along to the model's `from_pretrained(..., **model_kwargs)` function.
            pipeline_kwargs {Optional[Dict[str, Any]]} -- Additional keyword arguments passed along
                to the specific pipeline init (see the documentation for the corresponding pipeline class
                for possible values).

        Note that this model will be downloaded from the Hugging Face model hub.
        """
        super().__init__(
            ai_model_id=ai_model_id,
            task=task,
            device=(f"cuda:{device}" if device >= 0 and torch.cuda.is_available() else "cpu"),
            generator=transformers.pipeline(
                task=task,
                model=ai_model_id,
                device=device,
                model_kwargs=model_kwargs,
                **pipeline_kwargs or {},
            ),
        )
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")

    async def complete_async(
        self,
        prompt: str,
        request_settings: HuggingFaceRequestSettings,
        **kwargs,
    ) -> Union[str, List[str]]:
        if kwargs.get("logger"):
            logger.warning("The `logger` parameter is deprecated. Please use the `logging` module instead.")
        try:
            results = self.generator(**request_settings.prepare_settings_dict(prompt=prompt))
            result_field_name = "summary_text" if self.task == "summarization" else "generated_text"
            if len(results) == 1:
                return results[0][result_field_name]
            return [resp[result_field_name] for resp in results]

        except Exception as e:
            raise AIException("Hugging Face completion failed", e)

    async def complete_stream_async(
        self,
        prompt: str,
        request_settings: HuggingFaceRequestSettings,
        **kwargs,
    ):
        """
        Streams a text completion using a Hugging Face model.
        Note that this method does not support multiple responses.

        Arguments:
            prompt {str} -- Prompt to complete.
            request_settings {HuggingFaceRequestSettings} -- Request settings.

        Yields:
            str -- Completion result.
        """
        if kwargs.get("logger"):
            logger.warning("The `logger` parameter is deprecated. Please use the `logging` module instead.")
        if request_settings.num_return_sequences > 1:
            raise AIException(
                AIException.ErrorCodes.InvalidConfiguration,
                "HuggingFace TextIteratorStreamer does not stream multiple responses in a parseable format. \
                    If you need multiple responses, please use the complete_async method.",
            )
        try:
            tokenizer = transformers.AutoTokenizer.from_pretrained(self.ai_model_id)
            streamer = transformers.TextIteratorStreamer(tokenizer)
            args = {prompt}
            kwargs = {
                "num_return_sequences": request_settings.num_return_sequences,
                "generation_config": request_settings.get_generation_config(),
                "streamer": streamer,
                "do_sample": request_settings.do_sample,
            }

            # See https://github.com/huggingface/transformers/blob/main/src/transformers/generation/streamers.py#L159
            thread = Thread(target=self.generator, args=args, kwargs=kwargs)
            thread.start()

            for new_text in streamer:
                yield new_text

            thread.join()

        except Exception as e:
            raise AIException("Hugging Face completion failed", e)
