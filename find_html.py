# -*- coding: utf-8 -*-
# @Time    : 2018/11/23 9:25
# @Author  : yueconger
# @File    : find_html.py
import re
import os

html_path = r'E:\LocalServer\LvPin\html\severance_pay/'
html_path_new = 'E:\LocalServer\LvPin\html/ld/劳动_离职时的经济补偿金/'


def find_id():
    xml_path = r'E:\LocalServer\LvPin\files\ld\tree_离职时的经济补偿金.xml'
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    re_rule = '<report iw="99">(.*?)</report>'
    all_id = re.findall(re_rule, content)
    return all_id


def get_html():
    list = os.listdir(html_path)  # 列出文件夹下所有的目录与文件
    if not os.path.exists(html_path_new):
        os.makedirs(html_path_new)
    all_id = find_id()
    print(all_id)
    count = 0
    for i in range(0, len(list)):
        path = os.path.join(html_path, list[i])
        print(path)
        html_name = path.split('/')[-1].split('.')[0]
        new_path = ''.join([html_path_new, html_name, '.html'])
        if html_name in all_id:
            with open(path, 'r', encoding='utf-8') as f:
                temp = f.read()
            with open(new_path, 'w', encoding='utf-8') as n:
                n.write(temp)
            print(html_name, '写入成功!')
            count += 1
    print(count)


def main():
    get_html()


if __name__ == '__main__':
    main()
