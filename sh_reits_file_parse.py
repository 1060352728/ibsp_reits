import pdfplumber

from langchain.chat_models import init_chat_model
from langchain.text_splitter import RecursiveCharacterTextSplitter
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
from fastapi.responses import JSONResponse


class QuestionRequest(BaseModel):
    file_name: str

app = FastAPI()


def extract_pdf_content(file_name: str):
    pdf_path = "./sh/2025-07-13/{}".format(file_name)
    text, tables = "", []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
            for table in page.extract_tables():
                markdown_table = "\n".join("| " + " | ".join(str(cell) for cell in row) + " |" for row in table)
                tables.append(f"表格：\n{markdown_table}\n")
    content = text + "\n".join(tables)

    # 2. 分块处理
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\n\n", "\n", "表格："]
    )   
    return text_splitter.split_text(content)

def get_parse_result(chunks):
    llm = init_chat_model(model="qwen3:8b", model_provider="ollama")
    vector_db = Chroma.from_texts(
        texts=chunks,
        embedding=OllamaEmbeddings(model="nomic-embed-text")
    )
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

    rag_chain = (
        {"context": vector_db.as_retriever(search_kwargs={"k": 4}), 
        "question": RunnablePassthrough()}
    ) | prompt | llm

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

            **重要**: 只需要返回下面的json格式数据，不要返回其他思考内容；输出格式示例如下:
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
    return rag_chain.invoke(questions)

@app.post("/ask/")
async def ask_question(request: QuestionRequest):
    """向大模型提问关于PDF内容的问题"""
    chuncks = extract_pdf_content(request.file_name)
    result = get_parse_result(chuncks)
    return JSONResponse(content={"answer": result.content})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)