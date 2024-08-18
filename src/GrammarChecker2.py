import textwrap
import chainlit as cl
from langchain_openai import ChatOpenAI

import os

from dotenv import load_dotenv

load_dotenv()

from src.DialogueAgent import DialogueAgent

class GrammarChecker:
    def __init__(self):
        model = ChatOpenAI(
            base_url=os.environ.get("GC_BASE_URL"),
            api_key=os.environ.get("GC_API_KEY"),
            model=os.environ.get("GC_MODEL") or 'gpt-4o-mini',
            max_tokens=512,
            max_retries=2,
            temperature=0.1
        )
        
        with open("prompts/grammar_correction.txt", "r") as f:
            system_prompt = f.read().replace('\n','\n    ')
            
            
        self.agent = DialogueAgent(
            ai_name='GrammarChecker',
            user_name='Student',
            system_prompt=system_prompt,
            model=model,
            history_length=2)
        
    @cl.step(type="llm")
    async def grammar_check(self, msg):
        current_step = cl.context.current_step
        
        result = ''
        
        #print(prompt)
        async for chunk in self.agent.astream_chat(msg):
            await current_step.stream_token(chunk)
            result += chunk

        return result 
