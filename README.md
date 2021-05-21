# QZone_Spider

新增数据字段：点赞数、浏览量、转发数、tid

TODO：规避反爬系统，并改进为多线程爬虫。

本项目为一个QQ空间说说获取爬虫，基于Python。  
This is a Python-based spider to get data from qzone.com  

以下为项目内主要文件的功能介绍。  
Here are descriptions about functions of files in this project.   

1. QZone_Spider.py  
	爬虫主程序的Python脚本  
	Python srcipt of this spider  
	
2. Json_spliter.py  
	Json文件分割脚本，可避免单个内容文件过大  
	A Json file spliter to split large file  
	
3. /data  
	获取的部分公开空间的说说内容  
	Some data obtained from public Qzones  

关于具体的项目描述与实现过程，请参考[教程](https://ericzhu-42.github.io/2019/05/01/QQ-Zone-Spider/)。  
For detailed descriptions, please visit [this tutorial](https://ericzhu-42.github.io/2019/05/01/QQ-Zone-Spider/). (Chinese version)  