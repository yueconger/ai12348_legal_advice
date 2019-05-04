# -*- coding: utf-8 -*-
# @Time    : 2018/12/7 9:30
# @Author  : yueconger
# @File    : handle_content.py
import re
import os

FILEPATH = r"F:\婚姻_小孩问题\小孩问题/"
FILEPATHNEW = r"F:\婚姻_小孩问题\小孩问题_new/"

class HandleContent(object):
    def __init__(self):
        self.filepath = FILEPATH
        self.filepath_new = FILEPATHNEW

    def process_html(self):
        html_list = os.listdir(self.filepath)  # 列出文件夹下所有的目录与文件
        count = 0
        print(len(html_list))

        re_rule_shan = '<h1>.*?友情链接</h1>[\s\S]*'
        re_rule_shan_1 = '（<strong>友情链接部分有离婚起诉状自动生成链接供你使用</strong>）'
        re_rule_shan_2 = '<p><a href="/g/susongfei_calculator/\?action=restart" target="_blank">[\s\S]<strong>【诉讼费计算器】</strong></a></p>'
        re_rule_fuyang = '抚养费在：<strong>(.*?)</strong>'
        sub_fuyang = '抚养费在：<strong>Alimony</strong>'

        re_rule_date = '是(.*?)出生的现有年龄是<strong>(.*?)</strong>'
        re_rule_date_1 = '是(.*?)出生的现有年龄是（<strong>(.*?)</strong>）'
        sub_date = '是<strong>Year</strong>出生的现有年龄是<strong>Age</strong>'

        re_rule_susong = '诉讼费在（<strong>(.*?)</strong>）左右'
        sub_susong = '诉讼费在（<strong>LegalCost</strong>）左右'

        for i in range(0, len(html_list)):
            html_path = os.path.join(self.filepath, html_list[i])

            with open(html_path, "r", encoding="utf-8") as rf:
                content = rf.read()
            flag_shan = self.handle_regular(re_rule_shan, content)
            flag_shan1 = self.handle_regular(re_rule_shan_1, content)
            flag_shan2 = self.handle_regular(re_rule_shan_2, content)
            content = self.process_content(flag_shan, re_rule_shan, content)
            content = self.process_content(flag_shan1, re_rule_shan_1, content)
            content = self.process_content(flag_shan2, re_rule_shan_2, content)
            re_rule_fanben = '<h.*?>.*?相关申请书（范本）</h.*?>[\s\S]*?<div class="drop\-list">[\s\S]*?</style>'
            flag_fanben = self.handle_regular(re_rule_fanben, content)
            content = self.process_content(flag_fanben, re_rule_fanben, content)

            content = self.modify_content(re_rule_susong, sub_susong, content)
            content = self.modify_content(re_rule_fuyang, sub_fuyang, content)
            res = re.findall(re_rule_date, content)
            if len(res) > 0 :
                content = self.modify_content(re_rule_date, sub_date, content)
            else:
                content = self.modify_content(re_rule_date_1, sub_date, content)

            html_new_path = os.path.join(self.filepath_new, html_list[i])
            with open(html_new_path, "w", encoding="utf-8") as wf:
                wf.write(content)
                print(html_list[i], "写入成功!")
        print(count)

    def handle_regular(self, re_rule, content):
        """
        匹配正则表达式
        :return flag
        """
        res = re.findall(re_rule, content)
        flag = 0
        if len(res) > 0:
            print("匹配到结果有%s个" % len(res))
            flag = 1
        else:
            print('未匹配到')
        return flag

    def delete_content(self, delete_con, content):
        """
        删除不需要部分
        :return: 删除后文本内容
        """
        content_new = re.sub(delete_con, '', content)
        return content_new

    def modify_content(self, con, mo_con, content):
        """
        修改传递值部分
        :return: 修改后的文本内容
        """
        content_new = re.sub(con, mo_con, content)
        return content_new

    def process_content(self, flag, re_rule, content):
        if flag == 1:
            content = self.delete_content(re_rule, content)
        else:
            pass
        return content


if __name__ == '__main__':
    hc = HandleContent()
    hc.process_html()
