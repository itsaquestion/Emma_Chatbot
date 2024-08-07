import chainlit as cl

from openai import AsyncOpenAI

import os


from dotenv import load_dotenv


import chainlit as cl

from src.utils import get_final_assessment, extract_letters

from src.GrammarChecker import GrammarChecker


os.environ["HTTP_PROXY"] = "http://127.0.0.1:5035"
os.environ["HTTPS_PROXY"] = os.environ["HTTP_PROXY"]

gc = GrammarChecker()

# 从 .env 文件加载环境变量
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")

# 创建 AsyncOpenAI 实例
chat_client = AsyncOpenAI(api_key=api_key, base_url=base_url)


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if (username, password) == ("admin", "admin"):
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None


chat_settings = {
    # "model": "gpt-3.5-turbo",
    "model": "anthropic/claude-3-haiku",
    "temperature": 0.7,
    "max_tokens": 500,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}


@cl.on_chat_start
def start_chat():
    with open("teacher_system.txt", "r") as f:
        text = f.read()

    cl.user_session.set(
        "message_history",
        [
            {
                "role": "system",
                "content": text,
            }
        ],
    )


@cl.on_message
async def main(message: cl.Message):
    check_result = ""

    if len(message.content) < 500:
        # print("[Do check]")
        check_result: str = await gc.grammar_check(message.content)

    # check_result = '\n'.join(["> " + x for x in check_result.split('\n')])
    # print(check_result)
    # print(get_final_assessment(check_result))

    if check_result != "" and get_final_assessment(check_result).lower() != "yes":
        await cl.Message(content="**[grammar check]**\n" + check_result).send()
    else:
        message_history = cl.user_session.get("message_history")
        message_history.append({"role": "user", "content": message.content})

        msg = cl.Message(content="")

        await msg.send()

        stream = await chat_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://py4ss.net",  # Optional, for including your app on openrouter.ai rankings.
                "X-Title": "Emma",  # Optional. Shows in rankings on openrouter.ai.
            },
            messages=message_history,
            stream=True,
            **chat_settings,
        )

        async for part in stream:
            if token := part.choices[0].delta.content or "":
                await msg.stream_token(token)

        message_history.append({"role": "assistant", "content": msg.content})
        await msg.update()
