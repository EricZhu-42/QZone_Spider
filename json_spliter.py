import sys
import json
count = 0
split_size = 40000
name = "NJU_QFX"

data_path = sys.path[0] + "/data/"

with open(data_path + "{}.json".format(name),'r',encoding='utf-8') as f:
    json_data = json.loads(f.read())

new_data = dict()
for index in json_data:
    new_data[index] = json_data[index]
    if len(new_data)>split_size:
        with open(data_path + "{}_part_{:d}.json".format(name,count),'w+',encoding='utf-8') as f:
            f.write(json.dumps(new_data,indent=4,ensure_ascii=False))
        count += 1
        new_data = dict()
if count!=0:
    with open(data_path + "{}_part_{:d}.json".format(name,count),'w+',encoding='utf-8') as f:
        f.write(json.dumps(new_data,indent=4,ensure_ascii=False))