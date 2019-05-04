# -*- coding: utf-8 -*-
# @Time    : 2018/11/26 4:37
# @Author  : yueconger
# @File    : et_proxy.py
import requests
import os


# a = os.system(r'etdaili.exe --server --showwnd --port=8222 --name=congcong --pwd=Btwmm233@')
#
# print(a)

# ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
# headers = {
#         'user-agent': ua
#     }

def get_info(url):
    response = requests.get(url)
    return response.content.decode()


def change_proxy():
    # url = 'http://127.0.0.1:8222/connect/?province=福建省&city=泉州市&linktype=0[0:softe 1:l2tp 2:open]'  # 固定城市所在地获取代理IP
    url = 'http://127.0.0.1:8222/connect/?linktype=0[0:softe 1:l2tp 2:open]'  # 随机获取代理IP
    response = requests.get(url)
    print('now', response.content.decode())
    state = '代理更换完毕'
    flag = 0
    while flag < 1:
        getstate = 'http://127.0.0.1:8222/getstate/'
        res = get_info(getstate)
        print(res)
        if '已连接' in res:
            flag = 1
            # print('代理更换成功')
            return state
