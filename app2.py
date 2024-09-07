# 改写成语音版

# %%

from operator import itemgetter
import textwrap
from typing import List
from prompt_poet import Prompt
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableLambda
from langchain.schema.runnable.config import RunnableConfig
from langchain.memory import ConversationBufferMemory

from chainlit.types import ThreadDict
import chainlit as cl

from src.utils import get_final_assessment, extract_letters

from src.GrammarChecker2 import GrammarChecker

import os

from src.DialogueAgent import DialogueAgent

from src import tts

# @cl.password_auth_callback
# def auth_callback(username: str, password: str):
#     # Fetch the user matching username from your database
#     # and compare the hashed password with the value stored in the database

#     if (username, password) == (os.environ['USERNAME'], os.environ['PASSWORD']):
#         return cl.User(
#             identifier=username, metadata={"role": "admin", "provider": "credentials"}
#         )
#     else:
#         return None



def make_teacher():
    sys_msg = """You are a English Teacher. You are talking to a student who is learning English.
    You need to check the grammar of the student's answer and provide feedback to the student. Lead the Student to continue talking. Be engaged.
    """

    model = ChatOpenAI(
        base_url=os.environ.get("CHAT_BASE_URL"),
        api_key=os.environ.get("CHAT_API_KEY"), # type: ignore
        model=os.environ.get("CHAT_MODEL") or "gpt-4o-mini",
        streaming=True,
        max_retries=512,
    )

    english_teacher = DialogueAgent(
        ai_name="Teacher", user_name="Student", system_prompt=sys_msg, model=model
    )
    
    return english_teacher

@cl.on_chat_start
async def on_chat_start():
    
    teacher = make_teacher()
    
    gc = GrammarChecker()
    
    chat_history = []
    
    cl.user_session.set("chat_history", chat_history)
    cl.user_session.set("teacher", teacher)
    cl.user_session.set("gc", gc)
    
# @cl.on_chat_resume
# async def on_chat_resume(thread: ThreadDict):
#     memory = ConversationBufferMemory(return_messages=True)
#     root_messages = [m for m in thread["steps"] if m["parentId"] == None]
#     for message in root_messages:
#         if message["type"] == "user_message":
#             memory.chat_memory.add_user_message(message["output"])
#         else:
#             memory.chat_memory.add_ai_message(message["output"])

#     cl.user_session.set("memory", memory)

#     setup_runnable()

# @cl.action_callback("action_button")
# async def on_action(action):
#     await cl.Message(content=f"Executed {action.name}").send()
#     # Optionally remove the action button from the chatbot user interface
#     await action.remove()


@cl.on_message
async def on_message(message: cl.Message):

    teacher: DialogueAgent = cl.user_session.get("teacher")  # type: ignore
    chat_history: List = cl.user_session.get("chat_history")  # type: ignore

    
    temp_prompt = teacher.make_chat_prompt(message.content, chat_history)
    temp_prompt.truncate(truncation_step=2)
    print(temp_prompt.string)

    res = cl.Message(content="")

    full_response = ''
    async for chunk in teacher.astream_chat(message.content, chat_history):
        await res.stream_token(chunk)
        full_response += chunk

    await res.send()
    
    # 使用edge-tts
    audio_data = await tts.ms_tts_stream(full_response)

    # 使用gpt-sovits
    # audio_data = await tts.gpt_sovits_tts_stream(full_response)

    # 添加音频控件并自动播放语音
    output_audio_el = cl.Audio(
        name="",
        auto_play=True,
        # mime=audio_mime_type,
        content=audio_data,
    )

    res.elements = [output_audio_el]
    await res.update()

    # print(memory.chat_memory.messages)
