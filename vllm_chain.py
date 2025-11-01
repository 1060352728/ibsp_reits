# 加载模型（通过 Ollama 进行加速）
from langchain_ollama import OllamaLLM
# 定义提示模板和链
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
# 带记忆功能的链
from langchain.memory import ConversationBufferMemory
# 使用代理实现复杂任务
from langchain.agents import initialize_agent, Tool
from langchain_community.tools import DuckDuckGoSearchRun

# 初始化 Ollama 模型
llm = OllamaLLM(
    model="qwen3:8b",
    base_url="http://127.0.0.1:11434"
)

prompt_template = PromptTemplate(
    input_variables=["query"],
    template="""你是一个专业的技术顾问，请回答以下问题：{query}"""
)

# 使用新的 RunnableSequence 替代 LLMChain
chain = prompt_template | llm | StrOutputParser()

# 初始化记忆
memory = ConversationBufferMemory(memory_key="history", return_messages=True)

# 定义工具
tools = [
    Tool(
        name="Search",
        func=DuckDuckGoSearchRun().run,
        description="搜索网络信息"
    ),
    Tool(
        name="QA",
        func=lambda x: chain.invoke({"query": x}),
        description="回答技术问题"
    )
]

# 初始化代理
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)

# 调用代理
if __name__ == "__main__":
    print("=== 测试代理功能 ===")
    try:
        result = agent.invoke({"input": "解释量子计算的基本原理，并提供最近的研究进展"})
        print("代理回答:", result["output"])
    except Exception as e:
        print(f"运行出错: {e}")
        # 如果代理失败，尝试直接使用链
        try:
            result = chain.invoke({"query": "解释量子计算的基本原理"})
            print("直接回答:", result)
        except Exception as e2:
            print(f"直接调用也失败: {e2}")
    
    print("\n=== 测试带记忆的对话链 ===")
    # 创建带记忆的对话链
    def create_conversation_chain():
        return RunnablePassthrough.assign(
            history=lambda x: memory.load_memory_variables({})["history"]
        ) | prompt_template | llm | StrOutputParser()

    conversation_chain = create_conversation_chain()
    
    # 测试多轮对话
    questions = [
        "什么是人工智能？",
        "它与机器学习有什么关系？",
        "深度学习又是什么？"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n--- 第{i}轮对话 ---")
        print(f"问题: {question}")
        
        try:
            # 使用带记忆的对话链
            response = conversation_chain.invoke({"query": question})
            print(f"回答: {response}")
            
            # 保存对话到记忆
            memory.save_context(
                {"input": question},
                {"output": response}
            )
            
        except Exception as e:
            print(f"对话链出错: {e}")
            # 如果对话链失败，使用简单链
            try:
                response = chain.invoke({"query": question})
                print(f"简单回答: {response}")
            except Exception as e2:
                print(f"简单链也失败: {e2}")
    
    print("\n=== 显示对话历史 ===")
    print("记忆中的对话历史:")
    print(memory.load_memory_variables({}))