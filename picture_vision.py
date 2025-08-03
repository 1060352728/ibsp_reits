from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage    
import base64

llm = init_chat_model(model="qwen2.5vl:7b", model_provider="ollama")

with open("picture/1.JPG", "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

message = HumanMessage(
    content=[
        {"type": "text", "text": "描述一下这幅图,用中文回答"},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
        },
    ],
)
response = llm.invoke([message])
print(response.content)
