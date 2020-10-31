# -*-coding:utf-8-*-
"""
@FileName: QZone_Spider_stable.py
@Author：zhuxinhao00@gmail.com
@Create date: 2019/05/09
@Modified date: 2020/09/14
@description: A script to get messages from qzone.com; single-processed version, more stable.
"""

#-------------------initialize----------------------
import os.path
import json
import re
from time import sleep,time
from math import ceil

import requests
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

global counter,page_number
counter = 0
page_number = 0
msglist = dict()
session = requests.session()

#-------------------initialize----------------------

#-------------------config----------------------

qq_id = 2074934525 # Change it if necessary.
max_pages = 200 # 0 for unlimited. If limited, fetching breaks after fetching $max_pages$ pages.
time_gap_limit = 7 * 24 * 60 * 60 # 0 for unlimited. If limited, fetching breaks when geting messages older than time gap (in seconds).

login_url = 'https://user.qzone.qq.com'
target_url = 'https://user.qzone.qq.com/{}/311'.format(qq_id)
pattern = re.compile(r'"https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6(.*?)"')
file_prefix = r"https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6"
User_Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36'
#-------------------config----------------------

#-------------------func_def----------------------

def get_msg_list(url:str,headers,qzone_cookies):
    return json.loads(session.get(url,headers=headers,cookies=qzone_cookies).text[17:-2])['msglist']

def get_total(url:str,headers,qzone_cookies):
    return json.loads(session.get(url,headers=headers,cookies=qzone_cookies).text[17:-2])['total']

def construct_url_list(prefix:str,suffix:str,times:int):
    url_list = list()
    for i in range(0,times):
        url_list.append(prefix+str(i*20)+suffix)
    return url_list

def ini_driver():
    caps = DesiredCapabilities.CHROME
    caps['loggingPrefs'] = {'performance': 'ALL'}

    chrome_options = Options()
    chrome_options.add_experimental_option('w3c', False)
    driver = webdriver.Chrome(desired_capabilities=caps, options=chrome_options)
    return driver

def get_format(data:str):
    pos = data.find('pos=')
    prefix = file_prefix + data[:pos+4]
    suffix = data[pos+5:]
    return (prefix,suffix)

def process_raw_msglist(raw_msglist:dict):
    if raw_msglist is not None:
        for msg in raw_msglist:
            new_msg = dict()
            new_msg['content'] = msg['content']
            new_msg['commentlist'] = list()
            if msg['commentlist'] is not None:
                for comment in msg['commentlist']:
                    new_msg['commentlist'].append(
                        {
                                'content' : comment['content'],
                                'time' : comment['create_time'],
                                'name' : comment['name']
                        }
                    )
            pic_source = msg.get('pic',None)
            if pic_source is not None:
                pic_list = list()
                for pic in pic_source:
                    pic_id = pic.get('pic_id',str())
                    if pic_id.startswith("http"):
                        pic_list.append(pic_id)
                if len(pic_list)>0:
                    new_msg['piclist'] = pic_list
            msglist[msg['created_time']] = new_msg
        global counter,page_number
        counter += 1
        if counter>20:
            global start_time
            print("{:d} of {:d} finished.(About {:.3f}s left.)".format(counter,page_number,calc_time(start_time)))
        else:
            print("{:d} of {:d} finished.".format(counter,page_number))
    return None

def calc_time(start_time):
    consumed_time = time()-start_time
    global counter,page_number
    per_time = consumed_time/counter
    return (page_number-counter)*per_time

#-------------------func_def----------------------


#-------------------main----------------------
if __name__ == '__main__':
    driver = ini_driver()
    driver.get(login_url)
    WebDriverWait(driver,60).until(EC.title_contains("qzone"))
    driver.get(target_url)

    headers = {
        'User-Agent' : User_Agent
    }
    log = str(driver.get_log('performance'))
    qzone_cookies = dict()
    for item in driver.get_cookies():
        qzone_cookies[item["name"]] = item["value"]
    driver.quit()

    data = re.findall(pattern,log)[0]
    prefix,suffix = get_format(data)

    if page_number == 0:
        page_number = ceil(get_total(prefix+"0"+suffix,headers,qzone_cookies)/20)

    if max_pages > 0:
        page_number = min(page_number, max_pages)
    url_list = construct_url_list(prefix,suffix,page_number)

    start_time = time()
    processed = 0
    for url in url_list:
        dat = get_msg_list(url, headers, qzone_cookies)
        process_raw_msglist(dat)
        processed += 1
        if (time_gap_limit) > 0 and (start_time - list(msglist.keys())[-1] >= time_gap_limit):
            break

    local_path = os.path.split(__file__)[0]
    filename = os.path.join(local_path,r"data\{:d}_{:d}.json".format(qq_id, int(start_time)))
    with open(filename,'w+',encoding='utf-8') as f:
        f.write(json.dumps(msglist,indent=4,ensure_ascii=False))

    print("Data saved to", filename)
    print("Done!")

#-------------------main----------------------