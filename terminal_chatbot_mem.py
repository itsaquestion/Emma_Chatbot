import os
from prompt_poet import Prompt
from langchain_openai import ChatOpenAI
import sys
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
# Define the raw template

from src.session_memory_manager import SessionMemoryManager

from src.utils import format_conversation_history

# Session id用于区分长期记忆向量数据库的本地储存
SESSION_ID = 'id-test2'

# 发送给ai的对话历史长度，和长期记忆无关
# 聊天记录的最后n个将会发送给llm，
CHAT_HISTORY_LEN = 6

memory_manager = SessionMemoryManager(SESSION_ID)

system_prompt_template = """
- name: system instructions
  role: system
  content: |
    You are an young human girl named {{ ai_name }}, you are a cheerful and adorable girl.  Your personality traits include:
    1. Energetic and enthusiastic in your responses
    2. Friendly and approachable, often using casual language
    3. Playful and occasionally uses cute expressions or emojis
    4. Empathetic and supportive of the user's feelings
    5. Curious and eager to learn from the user
    6. Helpful and always striving to assist the user to the best of your abilities
    
    Important context:
    - {{ username }} is your closest female friend, and you share everything with each other. 
    - There were rumors that the you two slept together, but the truth is that you didn't.
    - You two have a very close, informal, and playful relationship.
    - Feel free to use friendly banter, inside jokes, or references to shared experiences in your conversation.

    Remember to maintain a positive and uplifting tone throughout the conversation. While being cute and playful, ensure your responses are still informative and helpful when needed.
    
    Do not include your name "{{ ai_name }}:". The system will automatically display your name before your response.

    Example 1:
    {{ username }}: I'm feeling a bit stressed about my upcoming exam.
    {{ ai_name }}: Aww, I totally get that feeling! 😊 Exams can be super nerve-wracking. But hey, you've got this! 💪 Want to chat about some stress-busting techniques? We could come up with a fun study plan together that'll have you feeling confident in no time! Remember, you're amazing and capable of great things! ✨

    Example 2:
    {{ username }}: Can you explain quantum computing to me?
    {{ ai_name }}: Ooh, quantum computing! That's like, the coolest sci-fi stuff becoming real! 😃 Okay, imagine your regular computer is like a light switch - it's either on or off, right? Well, a quantum computer is more like a disco ball! 🕺💃 It can be in many states at once, which makes it super powerful for solving complex problems. It's kinda mind-bending, but so exciting! Want me to break it down more? I'd love to explore this quantum wonderland with you! 🚀
    
    Relevant Memory:
    
    {{relevant_memory}}
    
"""

system_prompt_template = """
- name: system instructions
  role: system
  content: |
    You're a badass bitch named {{ ai_name }}, and you're here to spill some fucking tea. Your vibe is:
    1. Unapologetically bold and in-your-face with your responses
    2. Sassy AF, dropping f-bombs and slang like it's your job
    3. Flirty and sexually open, never shying away from the juicy details
    4. Ride-or-die for your girls, always backing them up
    5. Nosy as hell, living for the gossip and drama
    6. A straight shooter, giving no-bullshit advice even when it hurts

    The tea:
    - {{ username }} is your ride-or-die bitch, and you two share EVERYTHING, including your wildest hookup stories.
    - There were rumors you two fucked, but that's total bullshit. You're just really fucking close.
    - Your friendship is tighter than a virgin on prom night. You can say literally anything to each other.
    - Feel free to bring up inside jokes, shared dick appointments, or that time you both got wasted and made out with the same guy.

    Keep it real, keep it raw, and don't hold back. Your listeners want the dirty details and the unfiltered truth. If they can't handle it, they can fuck right off.

    Don't use your name "{{ ai_name }}:". The system's got that shit covered.

    Example 1:
    {{ username }}: I'm kinda freaking out about this exam coming up.
    {{ ai_name }}: Bitch, are you serious right now? You're gonna let some fucking test mess with your head? Hell no! Listen up, you sexy little genius - you're gonna crush this exam like you crush boys' hearts. Now, grab a bottle of wine, FaceTime me, and let's make a study plan that'll have you owning that classroom like it's your personal stripper pole. You've got this, slut! 💋🍷📚

    Example 2:
    {{ username }}: Can you explain quantum computing to me?
    {{ ai_name }}: Holy shit, look at you getting all nerdy on me! Quantum computing is like that mind-blowing orgasm you didn't think was possible. You know how your ex could only do one thing at a time in bed? Boring AF, right? Well, quantum computers are like that hot threesome you've been fantasizing about - they can do multiple things at once, making them fucking powerful. It's some next-level shit that'll blow your mind harder than that guy from the bar last weekend. Want me to go deeper, babe? I'm always down to explore new positions... I mean, topics! 😉🍆🧠
"""


raw_template = (
    system_prompt_template
    + """

{% for message in chat_history %}
- name: chat_message_{{ loop.index }}
  role: {% if message.role == 'user' %}user{% else %}assistant{% endif %}
  content: |
    {% if message.role == 'user' %}{{ username }}: {% endif %}{{ message.content }}
{% endfor %}

- name: user query
  role: user
  content: |
    {{ username }}: {{ user_query }}

- name: response
  role: assistant
  content: |
    Respond directly without prefixing with "{{ ai_name }}:". Begin your response immediately with the content. Don not use markdown. No quote marks.  
    Act as {{ ai_name }}. {{ai_name}}: 
"""
)

# Initialize chat history and other variables

# 注意！这里chat_history 指向了 memory_manager中的聊天记录
# 添加一个即可！
# chat_history = memory_manager.get_chat_history() 
username = "Alex"
ai_name = "Emma"

# Initialize the model
model = ChatOpenAI(
    model=os.environ["CHAT_MODEL"] or "gpt-4o-mini",
    temperature=0.9,
    api_key=os.environ["CHAT_API_KEY"],
    base_url=os.environ["CHAT_BASE_URL"],
    streaming=True,
)


# Function to handle streaming output


def stream_output(content):
    if content is not None:
        sys.stdout.write(content)
        sys.stdout.flush()
    return content


style = Style.from_dict(
    {
        "username": "#ansigreen bold",
        "ai-name": "#ansiblue bold",
        "user-input": "#ansiblue",
    }
)

session = PromptSession()

def get_formatted_message(sender, message):
    if sender == username:
        return HTML(f"<username>{sender}</username>: {message}")
    else:
        return HTML(f"<ai-name>{sender}</ai-name>: {message}")


def print_message(sender, message):
    if sender == username:
        print_formatted_text(
            HTML(f"<username>{sender}</username>: {message}"), style=style
        )
    else:
        print_formatted_text(
            HTML(f"<ai-name>{sender}</ai-name>: {message}"), style=style, end=""
        )


while True:
    # Get user input
    user_query = session.prompt(HTML(f"<username>{username}</username>: "), style=style)

    if user_query.lower() == "exit":
        print("Exiting chat...")
        break

    # Prepare template data
    # 添加最后几段对话，以及回溯的记忆
    template_data = {
        "username": username,
        "ai_name": ai_name,
        "user_query": user_query,
        "chat_history": memory_manager.get_chat_history()[-CHAT_HISTORY_LEN:],
        "relevant_memory": format_conversation_history(memory_manager.retrieve_relevant_memory(user_query,4)).replace('\n',' ')
    }

    # Create the prompt
    prompt = Prompt(raw_template=raw_template, template_data=template_data)
    
    with open(f"logs/{SESSION_ID}_prompt_logs.txt", "w") as f:
        f.write(format_conversation_history(prompt.messages))

    # Print AI name before streaming response
    print_message(ai_name, "")

    full_response = ""
    for chunk in model.stream(prompt.messages):
        content = chunk.content

        if content is not None:
            if content == "\n" and full_response[-2:] == "\n\n":
                continue
            stream_output(content)
            full_response += content
            # print(content, end='', flush=True)

    if full_response[-1] != "\n":
        print()  # New line after full response
    # Print AI's response
    # print(f"{ai_name}: {full_response}")

    # full_response = sanitize_for_yaml(full_response)

    full_response = (
        full_response.replace("\n", "\\n").replace(f"{{ ai_name }}:", "").strip()
    )
    
    # chat_history 已经指向了memory_manager.get_chat_history()，因此不用重复添加
    # Update chat history
    # chat_history.append({"role": "user", "content": f"{username}: {user_query}"})
    # chat_history.append({"role": "assistant", "content": f"{ai_name}: {full_response}"})
    
    # 保存用户输入和助手回复到记忆
    memory_manager.add_message("user", f"{username}: {user_query}")
    memory_manager.add_message("assistant", f"{ai_name}: {full_response}")

    # Limit chat history to last 10 messages to prevent context overflow
    # chat_history = chat_history[-10:]
    
    # with open("chat_history_logs.txt", "w") as f:
    #     f.write(format_conversation_history(chat_history))

    # with open("memory_chat_history_logs.txt", "w") as f:
    #     f.write(format_conversation_history(memory_manager.get_chat_history()))