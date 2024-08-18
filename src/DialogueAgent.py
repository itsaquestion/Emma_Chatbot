import os
from typing import List, Dict, AsyncGenerator
from prompt_poet import Prompt
from langchain_openai import ChatOpenAI

# Global prompt templates
CHAT_PROMPT_TEMPLATE = """
- name: system instructions
  role: system
  content: |
    {{ system_prompt }}

{% for message in chat_history %}
- name: chat_message_{{ loop.index }}
  role: {% if message.role == 'user' %}user{% else %}assistant{% endif %}
  content: |
    {% if message.role == 'user' %}{{ user_name }}: {% endif %}{{ message.content }}
{% endfor %}

- name: user query
  role: user
  content: |
    {{ user_name }}: {{ user_query }}

- name: response
  role: assistant
  content: |
    {{ai_name}}: """


class DialogueAgent:
    def __init__(
        self,
        ai_name: str = "Assistant",
        user_name: str = "User",
        system_prompt="You are a helpfull assistant.",
        model=ChatOpenAI(),
        history_length=10,
    ):
        self.ai_name = ai_name
        self.user_name = user_name
        self.system_prompt = system_prompt
        self.histroy_length = history_length

        # self.chat_history: List[Dict[str, str]] = []

        self.model = model

    def make_chat_prompt(
        self, message: str, chat_history: List[Dict[str, str]]
    ) -> Prompt:
        template_data = {
            "system_prompt": self.system_prompt,
            "user_name": self.user_name,
            "ai_name": self.ai_name,
            "user_query": message,
            "chat_history": chat_history[-self.histroy_length:],
        }

        prompt = Prompt(raw_template=CHAT_PROMPT_TEMPLATE, template_data=template_data)
        return prompt

    def chat(self, message: str, chat_history: List[Dict[str, str]]) -> str:
        prompt = self.make_chat_prompt(message, chat_history)
        response = self.model.invoke(prompt.messages)

        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": response.content})

        return response.content

    async def astream_chat(
        self, message: str, chat_history: List
    ) -> AsyncGenerator[str, None]:
        prompt = self.make_chat_prompt(message, chat_history)
        full_response = ""

        async for chunk in self.model.astream(prompt.messages):
            content = chunk.content
            full_response += content
            yield content

        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": full_response})
        


if __name__ == "__main__":
    import asyncio

    model = ChatOpenAI(
        base_url=os.environ.get("CHAT_BASE_URL"),
        api_key=os.environ.get("CHAT_API_KEY"),
        model=os.environ.get("CHAT_MODEL") or "gpt-4o-mini",
        streaming=True,
        max_retries=512,
    )

    async def main():
        agent = DialogueAgent(model=model)

        chat_history = []

        while True:
            user_input = input(f"{agent.user_name}: ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Ending the conversation. Goodbye!")
                break

            print(f"{agent.ai_name}: ", end="", flush=True)
            async for chunk in agent.astream_chat(user_input, chat_history):
                print(chunk, end="", flush=True)
            print()  # New line after the complete response

    asyncio.run(main())
