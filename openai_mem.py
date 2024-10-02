from openai import AsyncOpenAI
import chainlit as cl
import os

from src.session_memory_manager import SessionMemoryManager

from src.utils import format_conversation_history

# Session id用于区分长期记忆向量数据库的本地储存
SESSION_ID = "id-ui-teacher-test"

# 发送给ai的对话历史长度，和长期记忆无关
# 聊天记录的最后n个将会发送给llm，
CHAT_HISTORY_LEN = 6

memory_manager = SessionMemoryManager(SESSION_ID)

client = AsyncOpenAI(
    api_key=os.environ["CHAT_API_KEY"],
    base_url=os.environ["CHAT_BASE_URL"],
)


settings = {
    "model": os.environ["CHAT_MODEL"],
    "temperature": 0.7,
    "max_tokens": 500,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}


@cl.on_chat_start
def start_chat():
    cl.user_session.set(
        "message_history",
        [{"role": "system", "content": "You are a helpful assistant. "}],
    )


@cl.on_message
async def main(message: cl.Message):
    system_msg = """I would like you to act as my personal English tutor named Emma. My current English level is around A2-B1 on the CEFR scale, and my goal is to reach B1-B2 level. Please help me improve my English skills.
    
Relevant Memory:

"""

    system_msg += format_conversation_history(
        memory_manager.retrieve_relevant_memory(message.content, 10)
    ).replace("\n", " ")

    # 构造发送给LLM的对话
    # 这部应该是system_msg 加上 “UI上的对话（的末尾）”
    message_to_send = [
        {"role": "system", "content": system_msg}
    ] + cl.chat_context.to_openai()[-6:]

    message_to_send.append({"role": "user", "content": message.content})

    with open(f"logs/{SESSION_ID}_prompt_logs.txt", "w") as f:
        f.write(format_conversation_history(message_to_send))
        
    # 发送并接受回复
    msg = cl.Message(content="")

    stream = await client.chat.completions.create(
        messages=message_to_send, stream=True, **settings
    )

    full_response = ""
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)
            full_response += token

    # message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()

    memory_manager.add_message("user", f"{message.content}")
    memory_manager.add_message("assistant", f"{full_response}")
