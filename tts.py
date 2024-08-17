import edge_tts
import aiohttp




VOICE = "zh-CN-XiaoxiaoNeural"

# VOICE = "en-US-AriaNeural"


async def ms_tts_stream(text):
    communicate = edge_tts.Communicate(text, VOICE)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

async def gpt_sovits_tts_stream(text, text_language="zh", base_url="http://127.0.0.1:9880"):
    params = {
        "text": text,
        "text_language": text_language
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            if response.status == 200:
                audio_data = await response.read()
                return audio_data  # 直接返回 bytes
            else:
                raise Exception(f"Error: Received status code {response.status}")