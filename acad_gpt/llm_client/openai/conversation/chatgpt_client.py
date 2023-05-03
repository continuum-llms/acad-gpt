import logging

from langchain import LLMChain, OpenAI, PromptTemplate
from pydantic import BaseModel

from acad_gpt.llm_client.llm_client import LLMClient
from acad_gpt.llm_client.openai.conversation.config import ChatGPTConfig
from acad_gpt.memory.manager import MemoryManager
from acad_gpt.utils.openai_utils import get_prompt

logger = logging.getLogger(__name__)


class ChatGPTResponse(BaseModel):
    message: str
    chat_gpt_answer: str


class ChatGPTClient(LLMClient):
    """
    ChatGPT client allows to interact with the ChatGPT model alonside having infinite contextual and adaptive memory.

    """

    def __init__(self, config: ChatGPTConfig, memory_manager: MemoryManager):
        super().__init__(config=config)
        prompt = PromptTemplate(input_variables=["prompt"], template="{prompt}")
        self.chatgpt_chain = LLMChain(
            llm=OpenAI(
                temperature=config.temperature,
                openai_api_key=self.api_key,
                model_name=config.model_name,
                max_retries=config.max_retries,
                max_tokens=config.max_tokens,
            ),
            prompt=prompt,
            verbose=config.verbose,
        )
        self.memory_manager = memory_manager

    def converse(self, message: str, topk: int = 5, **kwargs) -> ChatGPTResponse:
        """
        Allows user to chat with user by leveraging the infinite contextual memory for fetching and
        adding historical messages to the prompt to the ChatGPT model.

        Args:
            message (str): Message by the human user.

        Returns:
            ChatGPTResponse: Response includes answer from th ChatGPT, conversation_id, and human message.
        """

        history = ""
        try:
            past_messages = self.memory_manager.get_messages(query=message, topk=topk, kwargs=kwargs)
            history = "\n".join([past_message.text for past_message in past_messages if getattr(past_message, "text")])
        except ValueError as history_not_found_error:
            logger.warning(f"Details: {history_not_found_error}")
        prompt = get_prompt(message=message, history=history)
        chat_gpt_answer = self.chatgpt_chain.predict(prompt=prompt)

        return ChatGPTResponse(message=message, chat_gpt_answer=chat_gpt_answer)
