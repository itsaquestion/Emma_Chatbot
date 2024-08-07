import chainlit as cl

from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI

import os

from dotenv import load_dotenv

load_dotenv()


class GrammarChecker:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=os.environ.get("GC_BASE_URL"),
            api_key=os.environ.get("GC_API_KEY"),
            model=os.environ.get("GC_MODEL") or 'gpt-4o-mini',
            max_tokens=500,
            max_retries=2,
        )
        
        with open("grammar_correction.txt", "r") as f:
            self.prompt = f.read()

    @cl.step(type="llm")
    def grammar_check(self, msg):
        current_step = cl.context.current_step
        
        messages = [
            (
                "system",
                self.prompt,
            ),
            ("human", msg),
        ]
        #current_step.output = self.llm.invoke(messages).content
        return self.llm.invoke(messages).content
