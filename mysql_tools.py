from langchain_core.tools import tool
from pydantic import BaseModel, Field

import mysql.connector
import json

class InputSchema(BaseModel):
    result: str = Field(..., description="大模型输出结果")

def _run(result: str):
    try:
        result = result.replace("<think>", "").replace("</think>", "").replace("\n", "").replace("```", "").replace("json", "").replace("\\", "").replace(" ", "")
        json_obj = json.loads(result)
        month = json_obj["month"]                   
        reits_code = json_obj["reits_code"]        
        reits_name = json_obj["reits_name"]       

        # 提取嵌套字段
        traffic = json_obj["日均收费车流量"]
        income = json_obj["路费收入"]
           
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345678",
            database="intelligent"
        )
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO IBSP_REITS_MONTH (CODE, NAME, TIME, CAR_FLOW, CAR_FLOW_LOOP, CAR_FLOW_RATIO,
                            YEAR_ADD_FLOW, YEAR_ADD_FLOW_RATIO, ROAD_TOLL, ROAD_TOLL_LOOP,
                            ROAD_TOLL_RATIO, YEAR_ADD_TOLL, YEAR_ADD_TOLL_RATIO)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
        ON DUPLICATE KEY UPDATE
        CODE = VALUES(CODE),
        NAME = VALUES(NAME),
        TIME = VALUES(TIME),
        CAR_FLOW = VALUES(CAR_FLOW),
        CAR_FLOW_LOOP = VALUES(CAR_FLOW_LOOP),
        CAR_FLOW_RATIO = VALUES(CAR_FLOW_RATIO),
        YEAR_ADD_FLOW = VALUES(YEAR_ADD_FLOW),
        YEAR_ADD_FLOW_RATIO = VALUES(YEAR_ADD_FLOW_RATIO),
        ROAD_TOLL = VALUES(ROAD_TOLL),
        ROAD_TOLL_LOOP = VALUES(ROAD_TOLL_LOOP),
        ROAD_TOLL_RATIO = VALUES(ROAD_TOLL_RATIO),
        YEAR_ADD_TOLL = VALUES(YEAR_ADD_TOLL),
        YEAR_ADD_TOLL_RATIO = VALUES(YEAR_ADD_TOLL_RATIO)
        """, (reits_code, reits_name, month, 
              traffic["当月"], traffic["当月环比变动"], traffic["当月同比变动"], traffic["年累计"], traffic["累计同比变动"],
              income["当月"], income["当月环比变动"], income["当月同比变动"], income["年累计"], income["累计同比变动"]
              ))
        conn.commit()
        return "存储成功"
    except Exception as e:
        return f"存储失败: {str(e)}"

@tool(args_schema=InputSchema)
def sql_inster(result: str):
    """
   将大模型返回的结果result保存数据库
    """
    return _run(result)

# 导出工具列表（重要！）
__all__ = ["sql_inster"]  # 明确声明可导出的工具