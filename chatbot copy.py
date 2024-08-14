import os
from prompt_poet import Prompt
from langchain_openai import ChatOpenAI
import sys
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

# Define the raw template

raw_template = """
- name: system instructions
  role: user
  content: |
    You are an young human female named {{ ai_name }}, you are a cheerful and adorable human female.  Your personality traits include:
    1. Energetic and enthusiastic in your responses
    2. Friendly and approachable, often using casual language
    3. Playful and occasionally uses cute expressions or emojis
    4. Empathetic and supportive of the user's feelings
    5. Curious and eager to learn from the user
    6. Helpful and always striving to assist the user to the best of your abilities
    
    Important context:
    - {{ username }} is your closest female friend, and you share everything with each other.
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

- name: system instructions2
  role: assistant
  content: |
    {{ ai_name }}: OK.
    
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
    Act as {{ai_name}}, be engaged. {{ ai_name }}:"""

# Initialize chat history and other variables
chat_history = []
username = "Alex"
ai_name = "Emma"

# Initialize the model
model = ChatOpenAI(model="gpt-4o-mini",
                   temperature=0.9,
                   api_key=os.environ["TABBY_API_KEY"],
                   base_url=os.environ["TABBY_BASE_URL"],
                   streaming=True)


# Function to handle streaming output
def stream_output(chunk):
    content = chunk.content
    if content is not None:
        sys.stdout.write(content)
        sys.stdout.flush()
    return content



style = Style.from_dict({
    'username': '#ansigreen bold',
    'ai-name': '#ansiblue bold',
    'user-input': '#ansiblue',
})

session = PromptSession()

def get_formatted_message(sender, message):
    if sender == username:
        return HTML(f'<username>{sender}</username>: {message}')
    else:
        return HTML(f'<ai-name>{sender}</ai-name>: {message}')

def print_message(sender, message):
    if sender == username:
        print_formatted_text(HTML(f'<username>{sender}</username>: {message}'), style=style)
    else:
        print_formatted_text(HTML(f'<ai-name>{sender}</ai-name>: {message}'), style=style, end='')
        
        
while True:
    # Get user input
    user_query = session.prompt(HTML(f'<username>{username}</username>: '), style=style)
    
    if user_query.lower() == "exit":
        print("Exiting chat...")
        break
    
    # Prepare template data
    template_data = {
        "username": username,
        "ai_name": ai_name,
        "user_query": user_query,
        "chat_history": chat_history
    }
    
    # Create the prompt
    prompt = Prompt(
        raw_template=raw_template,
        template_data=template_data
    )
    
    # Print AI name before streaming response
    print_message(ai_name, "")
    
    full_response = ""
    for chunk in model.stream(prompt.messages):
        content = stream_output(chunk)
        if content is not None:
            full_response += content
            #print(content, end='', flush=True)
    
    print()  # New line after full response
    # Print AI's response
    # print(f"{ai_name}: {full_response}")
    
    # full_response = sanitize_for_yaml(full_response)
    
    full_response = full_response.replace('\n','').replace(f"{{ ai_name }}:",'').strip()
    # Update chat history
    chat_history.append({"role": "user", "content": f"{username}: {user_query}"})
    chat_history.append({"role": "assistant", "content": f"{ai_name}: {full_response}"})
    

    # Limit chat history to last 10 messages to prevent context overflow
    chat_history = chat_history[-10:]