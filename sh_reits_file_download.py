# !/usr/bin/env python
# coding: utf-8
# Author:likui
# Date:2025-05-19
# Describe:上海交易所 月度和季度pdf文件下载，月度文件的关键字是“X月主要运营数据的公告”、季度文件的关键字是“X季度报告”

import sys
import os
import time
import logging
import datetime
import urllib.request

from selenium.webdriver.common.by import By
from pathlib import Path
from selenium import webdriver

#mac中的配置，后续删除
from selenium.webdriver.chrome.service import Service


#设置日志
logger_name = 'sh_reits'
logger = logging.getLogger(logger_name)
logger.setLevel(logging.INFO)
today = datetime.date.today().strftime('%Y-%m-%d')


log_dir = './logs/'
Path(log_dir).mkdir(parents=True, exist_ok=True)

log_path = log_dir + 'sh_reits_{}'.format(today) + '.log'
fh = logging.FileHandler(log_path)
fh.setLevel(logging.INFO)
fmt = "%(asctime)s %(levelname)s %(filename)s %(lineno)d %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt, datefmt)
fh.setFormatter(formatter)
logger.addHandler(fh)

def download_file(url, save_dir, filename):
    save_path = os.path.join(save_dir, filename)
    
    # 如果文件已存在，添加序号，防止文件名重复
    counter = 1
    while os.path.exists(save_path):
        name, ext = os.path.splitext(filename)
        save_path = os.path.join(save_dir, f"{name}_{counter}{ext}")
        counter += 1
    
    urllib.request.urlretrieve(url, save_path)
    logger.info(f"下载成功: {url} -> {save_path}")

def downfile():
    now = time.strftime("%Y-%m-%d", time.localtime())
    path = r'/Users/likui/workspace/python_workspace/ibsp_reits/sh/{}'.format(now)
    Path(path).mkdir(parents=True, exist_ok=True)

    pagenum = 1
    while True:
        logger.info(f'开始下载第{pagenum}页的数据')
        time.sleep(2)

        logger.info("开始获取表格数据")
        tbody = driver.find_element(By.XPATH,
                                value="/html/body/div[2]/div[2]/div/div/div/div[1]/div/div[2]/table/tbody")
        rows = tbody.find_elements(By.TAG_NAME, value='tr')
        logger.info("查询到记录数：" + str(len(rows)))
        if len(rows) == 0:
            break

        if len(rows) == 1 and len(rows[0].find_elements(By.TAG_NAME, value='td')) == 1:
            logger.info("暂无数据，程序退出")
            break
        
        for row in rows[0:]:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row)
            title = row.find_elements(By.TAG_NAME, value='td')[2].text
            if "月主要运营数据的公告" in title or "季度报告" in title:
                logger.info("查询title：" + title)
                link = row.find_elements(By.TAG_NAME, value='td')[2].find_elements(By.TAG_NAME, value='a')
                href = link[0].get_attribute("href")
                logger.info("下载链接地址为：" + href)
                dFileName = title + ".pdf"
                try:
                    download_file(href, path, dFileName)
                except Exception as e:
                    logger.error(e)
                    print(e)
            else:
                logger.info("非月度或者季度文件title：" + title)
                continue

        logger.info(f'第{pagenum}页的数据下载完成')

        # 获取下一页标签，如果没有，表示下载完成，跳出循环即可
        logger.info("开始点击下一页")
        next_div = driver.find_elements(By.XPATH, value='/html/body/div[2]/div[2]/div/div/div/div[1]/div/div[3]')
        next_page = next_div[0].find_elements(By.CLASS_NAME, value='next')
        
        if not next_page:
            logger.info(f"没有下一页，退出")
            break
        
        #下一页居中，防止点击不上
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page[0])
        next_page[0].click()
        pagenum += 1
        time.sleep(5)
    
if __name__ == '__main__':
    try:
        # 参数校验
        if len(sys.argv) != 4:
            logger.error('参数错误')

        args = sys.argv
        code = args[1]
        start_time = args[2]
        end_time = args[3]
        logger.info(f'上交所文件下载请求参数证劵代码{code}, 开始时间{start_time}, 结束时间{end_time}')

        chromeOptions = webdriver.ChromeOptions()
    
        chromeOptions.add_argument("--start-maximized")  # 启动时最大化窗口
        #mac
        service = Service("/usr/local/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chromeOptions)

        logger.info("加载上交所月度和季度文件下载页面")
        driver.get('https://www.sse.com.cn/reits/announcements/info/')
        time.sleep(2)

        # 设置缩放比例
        zoom_out = "document.body.style.zoom='1'"
        driver.execute_script(zoom_out)

        logger.info("设置证券代码")
        input_code = driver.find_element(By.ID, value='code')
        input_code.send_keys(code)
        time.sleep(2)

        logger.info("设置开始时间")
        input_startime = driver.find_element(By.ID, value='time')
        driver.execute_script("arguments[0].removeAttribute('readonly')", input_startime)
        input_startime.send_keys(start_time)
        time.sleep(2)

        logger.info("设置结束时间")
        input_endtime = driver.find_element(By.XPATH,
                                             value='/html/body/div[2]/div[2]/div/div/div/div[1]/div/div[1]/div[2]/div[1]/div/div[2]/span[2]/input')
        driver.execute_script("arguments[0].removeAttribute('readonly')", input_endtime)
        input_endtime.send_keys(end_time)
        time.sleep(5)
        
        logger.info("点击查询")
        qy_button = driver.find_element(By.XPATH,
                                        value='/html/body/div[2]/div[2]/div/div/div/div[1]/div/div[1]/div[2]/div[1]/div/button')
        
        webdriver.ActionChains(driver).move_to_element(qy_button).click(qy_button).perform()
        logger.info("查询完成")
        time.sleep(5)

        logger.info("开始下载文件")
        downfile()
        logger.info("下载完成")

        #下载完成标志，Java代码获取到该值表示下载完成
        print('0')
    except Exception as e:
        print('error')
        logger.info("下载上交所出错了:{}".format(e))
    finally:
        logging.shutdown()
        driver.quit()
