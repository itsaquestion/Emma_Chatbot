from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig

import chainlit as cl
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


@cl.on_chat_start
async def on_chat_start():
    model = ChatOpenAI( streaming=True)

    chat_histroy = InMemoryChatMessageHistory()
    cl.user_session.set("chat_histroy", chat_histroy)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You're an assistant who's name is Alex.",
            ),
            MessagesPlaceholder(variable_name="chat_histroy"),
            ("human", "{input}"),
        ]
    )
    runnable = prompt | model
    
    with_message_history = RunnableWithMessageHistory(
        runnable,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_histroy",
    )

    cl.user_session.set("with_message_history", with_message_history)


def get_session_history() -> BaseChatMessageHistory:
    return cl.user_session.get("chat_histroy")

@cl.on_message
async def on_message(message: cl.Message):
    runnable: Runnable = cl.user_session.get("with_message_history")

    msg = cl.Message(content="")

    async for chunk in runnable.astream(
        {"input": message.content},
        config=RunnableConfig(
            callbacks=[cl.LangchainCallbackHandler()],
        ),
    ):
        await msg.stream_token(chunk.content)

    await msg.send()

    print(cl.user_session.get("chat_histroy"))
