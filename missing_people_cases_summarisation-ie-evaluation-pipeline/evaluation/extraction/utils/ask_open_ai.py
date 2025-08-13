import os
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()
client =  OpenAI(api_key=os.getenv("OPEN_API_MLMI_KEY"))

def ask_open_ai(prompt, model="gpt-4o-mini", maxtokens=None, system_prompt="You are a helpful assistant that summarizes data."):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=maxtokens
    )
    print(response.choices[0].message.content)
    return response.choices[0].message.content