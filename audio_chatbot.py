# %%
from operator import itemgetter
import textwrap

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableLambda
from langchain.schema.runnable.config import RunnableConfig
from langchain.memory import ConversationBufferMemory
import edge_tts
from chainlit.types import ThreadDict
import chainlit as cl

from src.utils import get_final_assessment, extract_letters

from src.GrammarChecker import GrammarChecker

import os


def setup_runnable():
    #with open("prompts/teacher_system.txt", "r") as f:
    #    text = f.read()
        
    text = "你是一个友善的助手。你模仿女性人类的人类口语，风格活泼可爱，因此你的输出是口语化的纯文本，不会包括markdown格式标记，表格，或者列表，因为人类说话中不包括这些内容。"
    memory: ConversationBufferMemory = cl.user_session.get("memory")  # type: ignore
    model = ChatOpenAI(
        # base_url=os.environ.get("CHAT_BASE_URL"),
        # api_key=os.environ.get("CHAT_API_KEY"),
        model="gpt-4o-mini",
        streaming=True,
        max_retries=512,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", text),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{query}"),
        ]
    )

    runnable = (
        RunnablePassthrough.assign(
            history=RunnableLambda(memory.load_memory_variables) | itemgetter("history")
        )
        | prompt
        | model
        | StrOutputParser()
    )
    cl.user_session.set("runnable", runnable)


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True))
    cl.user_session.set("gc", GrammarChecker())
    setup_runnable()
    
VOICE = "zh-CN-XiaoxiaoNeural"

# TEXT = "The campaign said some of its internal communications had been hacked and suggested Iran was responsible and seeking to undermine the former president’s prospects in the November election."

# VOICE = "en-US-AriaNeural"


async def text_to_speech_stream(text):
    communicate = edge_tts.Communicate(text, VOICE)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

@cl.on_message
async def on_message(message: cl.Message):
    memory: ConversationBufferMemory = cl.user_session.get("memory")  # type: ignore

    runnable: Runnable = cl.user_session.get("runnable")  # type: ignore

    res = cl.Message(content="")

    full_response = ''
    
    async for chunk in runnable.astream(
        {"query": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await res.stream_token(chunk)
        full_response += chunk
    
    # 把对话内容加入memory
    memory.chat_memory.add_user_message(message.content)
    memory.chat_memory.add_ai_message(res.content)
    
    answer_message = await res.send()

    # TTS
    audio_data = await text_to_speech_stream(full_response)

    # 添加音频控件并自动播放语音
    output_audio_el = cl.Audio(
        name='',
        auto_play=True,
        #mime=audio_mime_type,
        content=audio_data,
    )

    answer_message.elements = [output_audio_el]
    await answer_message.update()

    # print(memory.chat_memory.messages)
