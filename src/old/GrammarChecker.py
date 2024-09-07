import textwrap
import chainlit as cl
from langchain_openai import ChatOpenAI

import os

from dotenv import load_dotenv

load_dotenv()

class GrammarChecker:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=os.environ.get("GC_BASE_URL"),
            api_key=os.environ.get("GC_API_KEY"),
            model=os.environ.get("GC_MODEL") or 'gpt-4o-mini',
            max_tokens=512,
            max_retries=2,
            temperature=0.1
        )
        
        with open("prompts/grammar_correction.txt", "r") as f:
            system_prompt = f.read()

        self.prompt = system_prompt
    

    @cl.step(type="llm")
    async def grammar_check(self, msg):
        current_step = cl.context.current_step
        
        result = ''

        prompt = self.prompt + textwrap.dedent(f"\nChat History:\n{msg}")
        
        # print(prompt)
        async for chunk in self.llm.astream(prompt):
            await current_step.stream_token(chunk.content)
            result += chunk.content

        return result 
