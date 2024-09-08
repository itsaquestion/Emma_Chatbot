# %%
from operator import itemgetter
import textwrap

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableLambda
from langchain.schema.runnable.config import RunnableConfig
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory


import chainlit as cl

from src.utils import (
    extract_final_score,
    xml_to_friendly_string,
    extract_idiomatic_rewrite,
)

from src.GrammarChecker2 import GrammarChecker

import os

from src import tts


def setup_runnable():
    with open("prompts/teacher_system.txt", "r") as f:
        text = f.read()

    memory = cl.user_session.get("memory")
    if not memory:
        memory = ConversationBufferWindowMemory(k=10)  # 如果内存不存在，创建一个新的
        cl.user_session.set("memory", memory)

    model = ChatOpenAI(
        base_url=os.environ.get("CHAT_BASE_URL"),
        api_key=os.environ.get("CHAT_API_KEY"),
        model=os.environ.get("CHAT_MODEL") or "gpt-4o-mini",
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


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True))
    cl.user_session.set("gc", GrammarChecker())
    setup_runnable()


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


@cl.on_message
async def on_message(message: cl.Message):
    gc: GrammarChecker = cl.user_session.get("gc")  # type: ignore
    memory: ConversationBufferMemory = cl.user_session.get("memory")  # type: ignore

    # =================================
    # 组合最后一条老师信息和学生的信息，给gc进行检查
    # =================================
    if len(memory.chat_memory.messages) > 0:
        reply = memory.chat_memory.messages[-1].content

        msg_for_gc = textwrap.dedent(f"Teacher: {reply} \nUser: {message.content}")

    else:
        msg_for_gc = f"""User: {message.content}
        """
    check_result = ""
    if len(message.content) < 500:
        # print("[Do check]")
        # check_result: str = await gc.grammar_check(message.content)
        check_result: str = await gc.grammar_check(msg_for_gc)

    # check_result = '\n'.join(["> " + x for x in check_result.split('\n')])
    # print(check_result)
    # print(get_final_assessment(check_result))

    full_response = ""

    # print(check_result)

    # =================================
    # 如果分数小于4，要求重写。否则进行正常对话
    # =================================
    if check_result != "" and extract_final_score(check_result.strip()) < 4:
        await cl.Message(content=xml_to_friendly_string(check_result)).send()
    else:
        await cl.Message(
            content="[**idiomatic rewrite**]: "
            + extract_idiomatic_rewrite(check_result)
        ).send()
        runnable: Runnable = cl.user_session.get("runnable")  # type: ignore

        res = cl.Message(content="")

        async for chunk in runnable.astream(
            {"query": message.content},
            config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
        ):
            await res.stream_token(chunk)
            full_response += chunk

        await res.send()

        memory.chat_memory.add_user_message(message.content)
        memory.chat_memory.add_ai_message(res.content)

        # =================================
        # TTS并显示控件
        # =================================

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
