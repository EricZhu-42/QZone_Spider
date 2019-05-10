# -*-coding:utf-8-*-

import configparser
import json
import os.path
from multiprocessing import Pool
from time import time

from aip import AipOcr

#-------------------config----------------------

process_number = 16
file_name = "NJU_QFX"
OCR_info_name = "OCR_info.ini"

#-------------------config----------------------

#-------------------initialize----------------------

global start_time,counter
counter = start_time = 0
new_data = dict()
local_path = os.path.split(__file__)[0]
config = configparser.ConfigParser()
config.read_file(open(os.path.join(local_path,OCR_info_name)))
APP_ID = config.get("OCR_info","APP_ID")
API_KEY = config.get("OCR_info","API_KEY")
SECRET_KEY = config.get("OCR_info","SECRET_KEY")
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

with open(os.path.join(local_path,r"data\{}.json".format(file_name)),'r',encoding='utf-8') as f:
    json_data = json.loads(f.read())
len_all = len(json_data)

#-------------------initialize----------------------

#-------------------func_def----------------------

def construct_sentence(response):
    words_result = response.get('words_result',None)
    if words_result is not None:
        words = [item['words'] for item in words_result]
        sentence = str()
        for word in words:
            sentence += word
        return sentence + ' '
    else:
        return str()

def get_response(msg_time,msg):
    piclist = msg.get('piclist',None)
    if piclist==None:
        return (msg_time,None)
    else:
        article = str()
        for pic_url in piclist:
            response = client.basicGeneralUrl(pic_url)
            article += construct_sentence(response)
        return (msg_time,article)

def add_to_list(return_data:tuple):
    msg_time = return_data[0]
    article = return_data[1]
    if article == None:
        new_data[msg_time]=json_data[msg_time]
    else:
        msg = json_data[msg_time]
        msg.pop('piclist')
        msg['content'] += article
        new_data[msg_time]= msg
    global counter
    counter += 1
    if counter>10:
        global start_time
        print("{:d} of {:d} finished.(About {:.3f}s left.)".format(counter,len_all,calc_time(start_time)))
    else:
        print("{:d} of {:d} finished.".format(counter,len_all))

def calc_time(start_time):
    consumed_time = time()-start_time
    global counter,len_all
    per_time = consumed_time/counter
    return (len_all-counter)*per_time

#-------------------func_def----------------------


#-------------------main----------------------

if __name__ == "__main__":

    print("File length =",len(json_data))
    items = json_data.keys()

    pos_pool = Pool(processes=process_number)
    for msg_time in items:
        pos_pool.apply_async(get_response,args=(msg_time,json_data[msg_time],),callback=add_to_list)
    print('Start')
    start_time = time()
    pos_pool.close()
    pos_pool.join()
    print('Done')

    if len(new_data)==len(json_data):
        print("Success!")
    else:
        print("Failed, current counter = {}.".format(counter))

    with open(os.path.join(local_path,r"data\pic_{}.json".format(file_name)),'w+',encoding='utf-8') as f:
        f.write(json.dumps(new_data,indent=4,ensure_ascii=False))
