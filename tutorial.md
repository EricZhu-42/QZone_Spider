## 前言

### 功能简介
本教程利用Python实现了一个简单的QQ空间说说抓取脚本。该脚本以每秒150~200条的速度抓取好友的历史说说，并将其格式化后存储至本地。

![04](misc\04.png)
![04](misc\05.png)

<!-- more -->

### 环境需求

1. Python 3.72
2. Python模块：[Selenium](<https://selenium-python.readthedocs.io/#>) 与 [Requests](<http://cn.python-requests.org/zh_CN/latest/>)
3. Google Chrome 74.0 与 ChromeDriver 74.0

> 注：具体版本号可酌情选择

## 你将在这里看到

1. 如何用Python实现对QQ空间说说数据的获取
2. 如何利用Chrome**开发者工具**分析动态网页
3. 如何利用Selenium完成对数据的请求与获取
4. 如何在Requests与Selenium间传递参数(如**Cookies**)
5. 如何完成一个简单的**多进程爬虫**

## 你将不会在这里看到

1. **如何安装**Python、Python模块与ChromeDriver等开发环境
2. **过于基础**的Python代码写法
3. Requests，Selenium，re，json等模块的**详细介绍**
4. 用Selenium实现**自动登陆**（然而以后可能会做）
5. 关于Python与第三方模块的**进阶用法**

## 关于思路的简单介绍

首先，观察QQ空间说说页面，可以发现说说页面为**动态网页**，无法用下载网页并解析的方式获取说说数据。通过对翻页时发送/接收数据的分析，我们可以找出存放说说**内容**的具体**文件**与其**请求方式**。

其次，我们利用**Selenium**进行初步的模拟获取，成功地自动获取了说说内容页面，并对内容进行解析与格式化存储，速度为每秒20~40条。

接着，为了提高获取的效率，我们利用**Requests**与**Multiprocessing**，用**多进程模式**重构了脚本，使获取的速度提高为每秒150~200条。

最后，我们对脚本的**功能**进行完善，添加预计剩余时间，大文件分割等功能。

## 网页内容分析

> 注：考虑到原项目的开发背景为对南京大学表白墙的数据分析，本文以“南京大学表白墙”为样例对象。

### 找到资源文件

进入[目标的QQ空间说说页面](<https://user.qzone.qq.com/2074934525/311>)，**查看网页源代码**，我们可以发现说说内容并未保存在网页源文件中。因此，我们的获取目标为动态页面的数据内容。

> 在动态页面中，数据内容一般在客户端与网页交互（如进入网页，点击翻页按钮）时发送到客户端，并通过JS脚本等途径动态插入到网页的<div\>标签中，从而完成对页面内容的更新。

我们打开Chrome浏览器的**开发者工具**，切换到**Network**标签页。此时我们可以获得交互过程中加载的所有资源。为了减少干扰，我们点击Network标签页下的**Clear**按钮，并在说说页面中切换到下一页。

![02](misc\02.png)

右侧列表中列出了翻页过程中加载的资源。在排除了无关的图片文件后，我们可以发现说说内容保存在名称为`emotion_cgi_msglist_v6`的文件中。该文件即为我们要获得的说说数据。

![03](misc\03.png)

### 找到请求模式

返回Network标签页，观察该文件的**请求头**与**请求参数**，可以看出：请求头中主要有**Cookies**和**User-Agent**两部分，而请求参数中出现了显眼的**pos**参数。通过翻页测试，我们发现pos参数符合以下规律：

> 第一页：pos = 0
> 第二页：pos = 20
> 第三页：pos = 40

因此，我们可以得出以下结论

> pos = 20 * 页码数 - 20

因此，我们接下来就将使用**Selenium**进行模拟登陆，并按照上述规律对文件进行获取。

## 基于Selenium的数据获取

为了便于调试，我们先利用Selenium登陆QQ空间，并且对文件进行请求。然后，我们将请求的数据进行格式化存储。

### 登陆

我们首先创建Selenium的webdriver实例，并用它打开QQ空间登陆界面，进入目标空间。

```python
import time
from selenium import webdriver

qq_id = 2074934525 # Change it if necessary.
login_url = 'https://user.qzone.qq.com'
target_url = 'https://user.qzone.qq.com/{}/311'.format(qq_id)

def ini_driver():
    driver = webdriver.Chrome()
    return driver

if __name__ == '__main__':
    driver = ini_driver()
    driver.get(login_url)
    time.sleep(5)
    driver.get(target_url)
```

### 请求资源

为了获取加载资源列表，我们需要调整Selenium的**DesiredCapabilities**特性，从而获得目标文件的请求细节。

```python
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

def ini_driver():
    caps = DesiredCapabilities.CHROME
    caps['loggingPrefs'] = {'performance': 'ALL'}
    driver = webdriver.Chrome(desired_capabilities=caps)
    return driver

log = str(driver.get_log('performance'))
```

通过分析请求，我们构造出请求的**匹配模式**，将完整的**请求体**匹配出来，并将完整请求拆分为 *prefix + page_pos + suffix* 的模式。

```python
import re

file_prefix = r"https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6"

def get_format(data:str):
    pos = data.find('pos=')
    prefix = file_prefix + data[:pos+4]
    suffix = data[pos+5:]
    return (prefix,suffix)

pattern = re.compile(r'"https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6(.*?)"')

data = re.findall(pattern,log)[0]
prefix,suffix = get_format(data)
```

此时，我们即可使用如下方式获得某一页的说说内容。

```python
page_pos = str(0)
content_url = prefix + page_pos + suffix
content = driver.get(content_url)
```

### 格式化与存储

上一步提取出的**content**为原始的目标文件。我们需要将其格式化为符合**json**规则的代码，并将其存储在文件中。

我们先利用字符串切片，除去开头结尾的无关字符。剩余内容为符合json规则的字符串，可以使用`json.loads`将其转化为json类型。此外，所有的说说内容都存放在`msglist`字段中。我们将其提取出来。

```python
import json

def get_msg_list(content:str):
    return json.loads(content[17:-2])['msglist']
```

接着，由于`msglist`字段中存在着大量的无关数据。我们用`msglist`字段中信息的有效部分构造`new_msg`，将它存放在字典中。

> 因为每条说说的发送时间唯一，我们以说说的timestamp(时间戳)属性作为字典索引。

```python
msglist = dict()

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
            msglist[msg['created_time']] = new_msg
    return None

```

此时，`msglist`即为我们需要的说说内容数据。我们将其保存在本地文件中。

> 为了能够正常保存中文数据，我们应当用UTF-8编码写入文件，并且在`json.dumps`方法中增加`ensure_ascii=False`参数。

 ```python
with open("{}.json".format(qq_id),'w+',encoding='utf-8') as f:
    f.write(json.dumps(msglist,indent=4,ensure_ascii=False))
 ```

通过遍历`page_pos`，我们即可完成对数据的自动获取工作。

## 用Requests实现多进程获取

由于Selenium的特性，我们一次只能获取一页数据。这种单进程模式对数据获取速度产生了较大的限制。此外，基于可视页面的ChromeDriver对系统资源的占用也较多。虽然可以通过**headless**启动或换用**PhantomJS**进行优化，但我们决定采用**Requests+Multiprocessing**的方法实现对数据的多进程获取。

### 构造Header

在分析网页内容时，我们观察了请求`emotion_cgi_msglist_v6`时的Header格式。我们首先构造出header的**User-Agent**部分。

```python
User_Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36'

headers = {
    'User-Agent' : User_Agent
    }
```

接着，我们对**Cookies**进行传递。我们利用`driver.get_cookies()`方法获得driver携带的所有cookie，并将其处理后保存为`qzone_cookies`字典。

```python
qzone_cookies = dict()
for item in driver.get_cookies():
    qzone_cookies[item["name"]] = item["value"]
```
> 在Cookies保存完后，可用`driver.quit()`退出webdriver，减少资源占用。

### 构造请求方法

为了便于用Multiprocessing进行多进程处理，我们先创建一个`Requests.session`，然后重写`get_msg_list`方法，将上一步中构造的Header与Cookies作为参数传递进去。

```python
import requests

session = requests.session()

def get_msg_list(url:str,headers,qzone_cookies):
    return json.loads(session.get(url,headers=headers,cookies=qzone_cookies).text[17:-2])['msglist']
```

### 配置进程池

接下来，我们创建Multiprocessing的**进程池(Pool)**。

```pyth
process_number = 8
pos_pool = multiprocessing.Pool(processes=process_number)
```

为了便于自动分配进程，我们构造`url_list`为获取地址的列表。

```python
def construct_url_list(prefix:str,suffix:str,times:int):
    url_list = list()
    for i in range(0,times):
        url_list.append(prefix+str(i*20)+suffix)
    return url_list

page_number = 10 # Change it if necessary.
url_list = construct_url_list(prefix,suffix,page_number)
```
在前两项准备工作结束后，我们就可以对进程池进行任务指派了。

```pythn
for url in url_list:
    pos_pool.apply_async(get_msg_list,args=(url,headers,qzone_cookies),callback=process_raw_msglist)
print("Start")
pos_pool.close()
pos_pool.join()
print('Done')
```

进程池会自动协调内部的进程，为每一个进程分配一个任务（此处为获取`url`的文件数据，在格式化后存入`msglist`字典中），并在任务结束后分配新的任务，直到`url_list`被完全遍历。

对于进程数为8的进程池，每秒可以获取约8~10页，即150~200条说说内容。现在，主要的工作已经完成了。

## 功能完善

在完成了主要功能的制作后，我们对程序的功能进行完善。

### 在登陆后自动跳转

我们刚刚使用`sleep(5)`作为登陆延时。但是，跳转到目标空间应该在登陆后自动进行。为此，我们引入selenium的**WebDriverWait**功能，在登陆后（即网页标题变化为 *xxx.qzone.com* 后）自动跳转至目标空间。

```python
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

if __name__ == '__main__':
    driver = ini_driver()
    driver.get(login_url)
    WebDriverWait(driver,60).until(EC.title_contains("qzone"))
    driver.get(target_url)
```



### 自动获取页面数量

先前的程序中，`url_list`的大小需要手动输入。对于理想的程序，`url_list`的大小应为说说页面的实际数量。通过观察，我们主要到目标说说的数量存放于`emotion_cgi_msglist_v6`文件的`total`字段中。由于一页最多有20条说说，我们可以用说说总数算出页面的数量。

```python
from math import ceil

def get_total(url:str,headers,qzone_cookies):
    return json.loads(session.get(url,headers=headers,cookies=qzone_cookies).text[17:-2])['total']

global page_number
page_number = 0 # Get all pages unless otherwise specified.
if page_number == 0:
    page_number = ceil(get_total(prefix+"0"+suffix,headers,qzone_cookies)/20)
```

### 估计剩余时间

在获取一定数量的页面数据，我们可以大致计算出获取每个页面所需要的时间，并借此算出预估的剩余时间。

```python
from time import time

global counter
counter = 0

def process_raw_msglist(raw_msglist:dict):
	if raw_msglist is not None:
        # Some duplicate code are left out.
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

if __name__ == '__main__':
    # Some duplicate code are left out.
    print("Start")
    start_time = time()
```

### 大文件分割

由于较大的数据集不便于网络传输，我们可以将生成的说说内容文件按一定的容量进行拆分。经过验证，40000条说说的大小约为30~40MB。以下给出拆分脚本的代码，供读者参考。

```python
import sys
import json
count = 0
split_size = 40000 # Change it if necessary
name = "NJU_BBQ" # Change it if necessary

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
```

## 后记

本教程的完整项目代码已在Github开源。地址如下：[项目地址](<https://github.com/EricZhu-42/QQ_Zone_Spider>)

