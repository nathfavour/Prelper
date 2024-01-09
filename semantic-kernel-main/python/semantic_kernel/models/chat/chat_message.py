"""Class to hold chat messages."""
from typing import TYPE_CHECKING, Dict, Optional

from pydantic import Field

from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.sk_pydantic import SKBaseModel

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext


class ChatMessage(SKBaseModel):
    """Class to hold chat messages."""

    role: Optional[str] = "assistant"
    fixed_content: Optional[str] = Field(default=None, init_var=False, serialization_alias="content")
    content_template: Optional[PromptTemplate] = Field(default=None, init_var=True, repr=False)

    @property
    def content(self) -> Optional[str]:
        """Return the content of the message."""
        return self.fixed_content

    async def render_message_async(self, context: "SKContext") -> None:
        """Render the message.
        The first time this is called for a given message,
        it will render the message with the context at that time.
        Subsequent calls will do nothing.
        """
        if self.fixed_content is None:
            if self.content_template is not None:
                self.fixed_content = await self.content_template.render_async(context)

    def as_dict(self) -> Dict[str, str]:
        """Return the message as a dict.
        Make sure to call render_message_async first to embed the context in the content.
        """
        return self.model_dump(exclude_none=True, by_alias=True, exclude={"content_template"})
