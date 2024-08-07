import chainlit as cl

from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI

import os

from dotenv import load_dotenv

load_dotenv()


class GrammarChecker:
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or os.getenv("GC_API_KEY")
        self.base_url = base_url or os.getenv("GC_BASE_URL")
        self.model = model or os.getenv("GC_MODEL") or "gpt-3.5-turbo"

        # print(base_url)

        # 创建 AsyncOpenAI 实例
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        with open("grammar_correction.txt", "r") as f:
            self.prompt = f.read()

    @cl.step(type="llm")
    async def grammar_check(self, msg, message_history=[]):
        checker_settings = {
            "model": self.model,
            "temperature": 0.5,
            "max_tokens": 500,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
        }

        prompt = self.prompt + "\n\n" + msg + "\n\nYour reply:"

        print(prompt)

        message_history.append({"role": "user", "content": prompt})
        stream = await self.client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://py4ss.net",  # Optional, for including your app on openrouter.ai rankings.
                "X-Title": "Emma",  # Optional. Shows in rankings on openrouter.ai.
            },
            messages=message_history,
            stream=True,
            **checker_settings,
        )

        current_step = cl.context.current_step
        # msg = cl.Message(content="")

        result = ""
        async for part in stream:
            delta = part.choices[0].delta

            if delta.content:
                # Stream the output of the step
                # current_step会输出到step的框中
                await current_step.stream_token(delta.content)

                # msg会输出到主对话框中
                # await msg.stream_token(delta.content)
                result += delta.content

        return result

    @cl.step(type="llm")
    def grammar_check2(self, msg):
        # prompt = self.prompt + "\n\n" + msg + "\n\nYour reply:"

        # template = (
        #     self.prompt
        #     + """{msg}

        # Your reply:"""
        # )

        # prompt = PromptTemplate.from_template(template)

        # print(prompt)

        llm = ChatOpenAI(
            base_url=os.environ.get("GC_BASE_URL"),
            api_key=os.environ.get("GC_API_KEY"),
            model=os.environ.get("GC_MODEL"),
            max_tokens=500,
            max_retries=2,
        )

        messages = [
            (
                "system",
                self.prompt,
            ),
            ("human", msg),
        ]

        return llm.invoke(messages).content
