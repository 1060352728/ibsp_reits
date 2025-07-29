"""
提供两个接口：
1:reits月度文件上传知识库
2:通过文件名获取上传文件的制定数据
"""

from contextlib import asynccontextmanager
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from fastapi.responses import JSONResponse
from fastapi import FastAPI
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain.chains import RetrievalQA
from langchain.schema import Document

import pdfplumber
import asyncio
from langchain.agents import initialize_agent, AgentType
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from mysql_tools import sql_inster

class QuestionRequest(BaseModel):
    file_name: str

# 知识库初始化函数
async def init_knowledge_base():
    def _sync_init():
        print("⏳ 正在初始化知识库...")
        return Chroma(
            embedding_function=OllamaEmbeddings(model="nomic-embed-text"),
            persist_directory="./finance_kb"
        )
    return await asyncio.to_thread(_sync_init)

# 1. 提取PDF内容（含表格）
def extract_pdf_content(pdf_path):
    text, tables = "", []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
            for table in page.extract_tables():
                markdown_table = "\n".join("| " + " | ".join(str(cell) for cell in row) + " |" for row in table)
                tables.append(f"表格：\n{markdown_table}\n")
    return text + "\n".join(tables)

# 文件上传知识库
def upload_file(file_name):
    file_path = "./sh/2025-07-13/{}".format(file_name)
    # 2. 分块处理
    content = extract_pdf_content(file_path)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\n\n", "\n", "表格："]
    )
    chunks = text_splitter.split_text(content)

    documents = []
    # 3. 为每个chunk添加文件标识元数据
    for chunk in chunks:
        document = Document(page_content=chunk, metadata={"file_id": file_name})
        documents.append(document)

    # 追加新文档
    app.state.vector_store.add_documents(documents)

    return JSONResponse(content={
        "status": "success",
        "file_id": file_name,
        "chunk_count": len(documents)
    })      

llm = init_chat_model(model="qwen3:8b", model_provider="ollama")

# 获取知识库信息
def get_parse_result(file_name):
    prompt = ChatPromptTemplate.from_template(
        """
        请分析以下数据（含表格）：
        ---
        {context}
        ---
        问题：{question}
        （如涉及表格，请用Markdown表格回复）
        """
        )
    
    # 创建带过滤的检索器
    retriever = app.state.vector_store.as_retriever(
        search_kwargs={"filter": {"file_id": file_name}}
    )

    # 构建QA链
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},  # 关键设置
        return_source_documents=True
    )
    
    questions = """
            你是一个专业的金融数据分析师，专门负责从公募REITS公告中提取关键运营数据。
            请从以下文本中提取所有符合要求的信息，如果某项信息不存在，请填写"null":
            需要提取的信息项如下：
            1. 月份 (如果适用)
            2. 公募REITS代码
            3. 公募REITS简称(简称不是全称，比如平安广州广河REIT，简称是广河REIT)
            4. 日均收费车流量当月
            5. 日均收费车流量当月环比变动
            6. 日均收费车流量当月同比变动
            7. 日均收费车流量年累计
            8. 日均收费车流量累计同比变动
            9. 路费收入当月
            10. 路费收入当月环比变动
            11. 路费收入当月同比变动
            12. 路费收入年累计
            13. 路费收入累计同比变动

            **重要**: 回答问题时必须按以下格式，不要返回其他思考内容；
            ```json
                {{
                    "month": "2024年1月",
                    "reits_code": "代码",
                    "reits_name": "简称",
                    "日均收费车流量": {
                        "当月":"",
                        "当月环比变动":"",
                        "当月同比变动":"",
                        "年累计":"",
                        "累计同比变动":"",
                        "日均收费车流量单位":""
                    },
                    "路费收入": {
                        "当月":"",
                        "当月环比变动":"",
                        "当月同比变动":"",
                        "年累计":"",
                        "累计同比变动":"",
                        "路费收入单位":""
                    }
                }}
            ```
            """
    return qa_chain({"query": questions})

tools = [sql_inster]

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """正确的异步上下文管理器实现"""
    try:
        # 异步初始化
        print("🟢 正在初始化知识库...")
        app.state.vector_store = await init_knowledge_base()
        # 关键点：必须有yield
        yield
    except Exception as e:
        print(f"🚨 初始化失败: {e}")
        raise    

app = FastAPI(lifespan=lifespan)

@app.post("/upload/")
async def ask_question(request: QuestionRequest):
    return upload_file(request.file_name)


@app.post("/ask/")
async def ask_question(request: QuestionRequest):
    result = get_parse_result(request.file_name)

    # 调用Tool存储结果
    agent.run(
        f"将大模型输出的结果result：{result['result']}存入数据库"
    )

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)