# -*- coding: utf-8 -*-
# @Time    : 2018/11/19 18:35
# @Author  : yueconger
# @File    : trans_report.py
import regex as re
import json
import requests
from conf import TYPE_SOFT

with open(r'E:\LocalServer\LvPin\files\hy\婚姻_起诉书 - 副本.xml', 'r', encoding='utf-8') as f:
    content = f.read()
with open(r'E:\bmsoft\咨询json\婚姻\ceshi\lvpin_12348.hy_起诉书_01.json', 'r', encoding='utf-8') as jf:
    json_list = json.load(jf)

xml_path = r'E:\LocalServer\LvPin\files\hy\tree_婚姻_起诉书_1.xml'


def trans(content):
    re_rule = '(?<=id_question="|item="|value=")(.*?)(?=")'
    content_list = list(set(re.findall(re_rule, content)))
    content_list = [i.split('||') for i in content_list]
    tmp = []
    for i in content_list:
        tmp.extend(i)
    content_list = list(set(tmp))
    def _foo(con):
        for i in json_list:
            if i.get(con):
                return i[con]
    for con in content_list:
        try:
            content = content.replace(con, _foo(con))
        except:
            print(con, _foo(con))
    return content

res_b = trans(content)

with open(xml_path, 'w', encoding='utf-8') as f:
    f.write(res_b)
