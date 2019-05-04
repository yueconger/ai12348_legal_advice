# -*- coding: utf-8 -*-
# @Time    : 2018/11/15 11:36
# @Author  : yueconger
# @File    : conf.py
import random
import string
import requests

FLAG = True

MONGODB_COL_AL = 'hy_离婚协议书'

FILEPATH_DOWN = r'E:\LocalServer\LvPin\测试/'

# TYPE_SOFT = 'divorce_agreement'
TYPE_SOFT = 'inherit'
FILENAME = r'E:\LocalServer\LvPin\测试\jicheng.xml'

# MONGODB_COL_AL = 'jc_继承纠纷'
#
# FILEPATH_DOWN = r'E:\LocalServer\LvPin\html\jc/'
#
# TYPE_SOFT = 'inherit'
# FILENAME = r'E:\LocalServer\LvPin\files\jc\jc_继承纠纷.xml'


def generate_random_str(randomlength=16):
    """
    生成一个指定长度的随机字符串，其中
    string.digits=0123456789
    string.ascii_letters=abcdefghigklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
    """
    str_list = [random.choice(string.digits + string.ascii_letters) for i in range(randomlength)]
    random_str = ''.join(str_list)
    return random_str


def formdata_tran(f_list):
    new_list = []
    for i in f_list:
        i = 'item%5B%5D=' + i
        new_list.append(i)
    new_str = '&'.join(new_list)
    return new_str


def get_session():
    type_sort = TYPE_SOFT
    url = 'https://ai.12348.gov.cn/g/' + type_sort
    headers = {
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
    }
    s = requests.Session()
    response = s.get(url, headers=headers)
    session = response.cookies
    cookies = session.items()
    cookie = '='.join(list(cookies[0]))
    return cookie


HEADERS = {
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'content-length': '0',
    'cookie': 'sessionid=bpw97me0pb844k2ba4fvvvns02k95gqv',
    'origin': 'https://ai.12348.gov.cn',
    'referer': 'https://ai.12348.gov.cn/g/where_to_divorce?',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Mobile Safari/537.36',
    'x-requested-with': 'XMLHttpRequest'
}

MONGDB_HOST = '127.0.0.1'
PORT = 27017
MONGODB_DBNAME = 'lvpin_12348'  # 数据库名