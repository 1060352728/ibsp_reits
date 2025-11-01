#from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

import base64


base_url='http://127.0.0.1:11434/v1/'

model="qwen2.5vl:7b"

api_key = "ollama"

llm = ChatOpenAI(base_url=base_url, model=model, api_key=api_key)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Usage
image_path = "/Users/likui/workspace/python_workspace/ibsp_reits/sh/2025-07-13/工银瑞信河北高速集团高速公路封闭式基础设施证券投资基金关于2025年3月主要运营数据的公告.pdf"
base64_image = encode_image(image_path)

# 准备消息
messages = [
    SystemMessage(content="你是一个有用的助手。"),
    HumanMessage(content=[
        {"type": "text", "text": "将改pdf中的内容以markdown格式输出，保留pdf中原有的格式"},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
    ])
]

# 调用模型
response = llm.invoke(messages)
print(response.content)


