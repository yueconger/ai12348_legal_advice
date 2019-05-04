# -*- coding: utf-8 -*-
# @Time    : 2018/11/15 11:36
# @Author  : yueconger
# @File    : request_ai.py
import re
import os
import sys
import json
import lxml
import requests
import conf
import time
import et_proxy
from urllib.request import urlretrieve
from pymongo import MongoClient
from conf import HEADERS, TYPE_SOFT, FILENAME, FLAG, FILEPATH_DOWN
from lxml import etree
from tree import Tree
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

'''
message = {
'iw': 5,
'id_question': id_question,
'item': [id1, id2, ...],
'val': [[val1, val2], [val21, val22], [val3]...]}
'''


class SpiderAi12348(object):
    def __init__(self):
        self.post_url = 'https://ai.12348.gov.cn/g/{type_sort}/?action_type=ajax'
        self.detail_url = ''
        self.headers = HEADERS
        data_item = ''
        self.form_data_click = {
            "item": data_item,
            "action": "next"
        }
        self.form_data_post = {
            "item[]": data_item,
            "action": "next"
        }

    def parse_url(self, cookie):
        type_sort = TYPE_SOFT
        self.headers['referer'] = 'https://ai.12348.gov.cn/g/' + type_sort + '?'
        self.headers['cookie'] = cookie
        res = requests.post(url=self.post_url.format(type_sort=type_sort), headers=self.headers, verify=False)
        response = res.content.decode()
        try:
            str_res = json.loads(response)
        except Exception as e:
            print('代理失效,需要更换', e)
            state = et_proxy.change_proxy()
            print(state)
            cookie = conf.get_session()
            self.headers['cookie'] = cookie
            res = requests.post(url=self.post_url.format(type_sort=type_sort), headers=self.headers, verify=False)
            response = res.content.decode()
            str_res = json.loads(response)
        return str_res, cookie

    def parse_post_url(self, cookie, form_data):
        # time.sleep(2)
        type_sort = TYPE_SOFT
        REQUEST_TIMEOUT = False
        NETWORK_STATUS = True

        self.headers['referer'] = 'https://ai.12348.gov.cn/g/' + type_sort + '?'
        self.headers['cookie'] = cookie
        try:
            res = requests.post(url=self.post_url.format(type_sort=type_sort), headers=self.headers, data=form_data,
                                timeout=10,
                                verify=False)
        except requests.exceptions.ConnectTimeout:
            NETWORK_STATUS = False
            print('网络连接失败')
            time.sleep(5)
            return
        except requests.exceptions.Timeout:
            REQUEST_TIMEOUT = True
            print('网络连接失败')
            time.sleep(5)
            return
        if REQUEST_TIMEOUT == True or NETWORK_STATUS == False:
            res = requests.post(url=self.post_url.format(type_sort=type_sort), headers=self.headers, data=form_data,timeout=10,
                                verify=False)
        response = res.content.decode()
        try:
            str_res = json.loads(response)
        except Exception as e:
            print(response, e)
            print('==============')
        else:
            return str_res

    def question_page(self, response, iw):
        str_res = etree.HTML(response)
        item = {}
        try:
            data_iw = str_res.xpath('//div[@class="question-ht"]/@data-iw')[0]  # 问题类型
            data_qid = str_res.xpath('//div[@class="question-ht"]/@data-qid')[0]  # 问题id
            data_con = str_res.xpath('//div[@class="question-ht"]/text()')[0].strip()  # 问题内容
            data_tip = str_res.xpath('//div[@class="question-ht"]/div[@class="tip"]/text()')  # 问题提示
        except Exception as e:
            print('session_id　已失效', e)
        else:
            item[data_qid] = data_con
            # self.save_id_con(item)
            if len(data_tip) > 0:
                data_con = ' '.join([data_con, data_tip[0].strip()])

            if iw == 1 or iw == 4:  # 单选
                message = self.choice_normal(iw, data_qid, response, data_con)
            if iw == 3:  # 文本框
                message = self.blank_input(iw, data_qid, response, data_con)
            if iw == 2:  # 多选
                message = self.choice_all(iw, data_qid, response, data_con)
            if iw == 5:  # 填空
                # 点击填入信息
                message = self.blank_fill(iw, data_qid, response, data_con)

            # 返回给算法接口
            return message

    def choice_normal(self, iw, data_qid, response, data_con):
        """
        单选与点击选择
        :return: 表单提交正常 item: 参数 action: next
        """
        if iw == 1:
            choice_flag = 0
            str_res = etree.HTML(response)
            choices_ht = str_res.xpath('//div[@class="mpage"]//div[@class="weui_cell_bd weui_cell_primary"]')
            c_list = []
            item_list = []
            item_list_txt = []
            value_list = []
            child = 'name="input_val_'
            if child in response:
                choice_flag = 1  # 有下级标签
                print('有下级标签')
            for choice in choices_ht:
                item = {}
                v_list = []
                choice_con = choice.xpath('./div[@class="ht"]/text()')[0].strip()
                choice_tip = choice.xpath('./div[@class="q-tip"]/text()')
                if len(choice_tip) > 0:
                    choice_con = ' '.join([choice_con, choice_tip[0].strip()])

                choice_id = choice.xpath('./div[@class="ht"]/@id')[0]
                try:
                    choice_id = choice_id.split('_')[-1]
                except Exception as e:
                    print('choice_id not find:', e)
                else:
                    # 判断是否有下级标签
                    if choice_flag == 1:
                        date_find = 'name="input_val_' + choice_id + '" type="date"'
                        money_find = 'name="input_val_' + choice_id + '" type="number"'
                        text_find = 'name="input_val_' + choice_id + '" type="text"'
                        choice_find = 'name="input_val_' + choice_id + '" type="hidden"'

                        if money_find in response:
                            input_val = self.choice_money()
                            v_list.append(input_val)
                            value_list.append(v_list)

                        elif date_find in response:
                            input_val = self.choice_date()
                            v_list.append(input_val)
                            value_list.append(v_list)

                        elif text_find in response:
                            input_val = '我想问这种是不是'
                            v_list.append(input_val)
                            value_list.append(v_list)

                        elif choice_find in response:
                            choice_find_fill = str_res.xpath('//div[@class="page-silder"]//p')
                            for i in choice_find_fill:
                                item = {}
                                choice_find_id_con = i.xpath('./text()')[0].strip()
                                # print(choice_find_id_con)
                                choice_find_id_id = i.xpath('./@data-id')[0]
                                # print(choice_find_id_id)
                                item[choice_find_id_id] = choice_find_id_con
                                self.save_id_con(item)
                                input_val = choice_find_id_id
                                v_list.append(input_val)
                            value_list.append(v_list)

                        else:
                            v_list = []
                            value_list.append(v_list)

                    # item[choice_id] = choice_con
                    # self.save_id_con(item)
                    c_list.append(item)
                    item_list.append(choice_id)
                    item_list_txt.append(choice_con)
            if choice_flag == 0:
                message = {
                    'iw': iw,
                    'id_question': data_qid,
                    'id_question_txt': data_con,
                    'items': item_list,
                    'items_txt': item_list_txt
                }
            else:
                message = {
                    'iw': iw,
                    'id_question': data_qid,
                    'id_question_txt': data_con,
                    'items': item_list,
                    'items_txt': item_list_txt,
                    'values': value_list
                }
        else:
            str_res = etree.HTML(response)
            choices_ht = str_res.xpath('//div[@class="weui_cell_bd weui_cell_primary"]')
            c_list = []
            item_list = []
            item_list_txt = []
            for choice in choices_ht:
                item = {}
                choice_con = choice.xpath('./div[@class="ht"]/text()')[0].strip()
                choice_tip = choice.xpath('./div[@class="q-tip"]/text()')
                if len(choice_tip) > 0:
                    choice_con = ' '.join([choice_con, choice_tip[0].strip()])

                choice_id = choice.xpath('./div[@class="ht"]/@id')[0]
                try:
                    choice_id = choice_id.split('_')[-1]
                except Exception as e:
                    print('choice_id not find:', e)
                else:
                    item[choice_id] = choice_con
                    self.save_id_con(item)
                    c_list.append(item)
                    item_list.append(choice_id)
                    item_list_txt.append(choice_con)
            message = {
                'iw': iw,
                'id_question': data_qid,
                'id_question_txt': data_con,
                'items': item_list,
                'items_txt': item_list_txt
            }
        return message

    def choice_all(self, iw, data_qid, response, data_con):
        """
        多选 表单提交 多个 item[]: 参数 action: next
        :return:
        """
        choice_flag = 0
        str_res = etree.HTML(response)
        choices_ht = str_res.xpath('//div[@class="mpage"]//div[@class="weui_cell_bd weui_cell_primary"]')
        c_list = []
        item_list = []
        item_list_txt = []
        value_list = []
        child = 'name="input_val_'
        if child in response:
            choice_flag = 1  # 有下级标签
            print('有下级标签')
        for choice in choices_ht:
            item = {}
            v_list = []
            try:
                choice_con = choice.xpath('./div[@class="ht"]/text()')[0].strip()
                choice_tip = choice.xpath('./div[@class="q-tip"]/text()')
            except Exception as e:
                print('在此处报错', e)
                print(response)
            if len(choice_tip) > 0:
                choice_con = ' '.join([choice_con, choice_tip[0].strip()])

            choice_id = choice.xpath('./div[@class="ht"]/@id')[0]
            try:
                choice_id = choice_id.split('_')[-1]
            except Exception as e:
                print('choice_id not find:', e)
            else:
                # 判断是否有下级标签
                if choice_flag == 1:
                    date_find = 'name="input_val_' + choice_id + '" type="date"'
                    money_find = 'name="input_val_' + choice_id + '" type="number"'
                    text_find = 'name="input_val_' + choice_id + '" type="text"'
                    text_find_2 = 'name="input_val_' + choice_id + '" rows="3"'
                    choice_find = 'name="input_val_' + choice_id + '" type="hidden"'  # 待添加选项

                    if money_find in response:
                        input_val = self.choice_money()
                        v_list.append(input_val)
                        value_list.append(v_list)

                    elif date_find in response:
                        input_val = self.choice_date()
                        v_list.append(input_val)
                        value_list.append(v_list)

                    elif text_find in response:
                        input_val = '我想问这种是不是'
                        v_list.append(input_val)
                        value_list.append(v_list)

                    elif text_find_2 in response:
                        input_val = '我想问这种是不是'
                        v_list.append(input_val)
                        value_list.append(v_list)

                    elif choice_find in response:
                        xpath_regular = '//div[@id="id_item_slider_{choice_id}"]//div[@class="widget_select"]//p'.format(choice_id=choice_id)
                        # xpath_regular = ''.join(["'", xpath_regular, "'"])
                        choice_find_fill = str_res.xpath(xpath_regular)
                        for i in choice_find_fill:
                            item = {}
                            choice_find_id_con = i.xpath('./text()')[0].strip()
                            # print(choice_find_id_con)
                            choice_find_id_id = i.xpath('./@data-id')[0]
                            # print(choice_find_id_id)
                            item[choice_find_id_id] = choice_find_id_con
                            self.save_id_con(item)
                            input_val = choice_find_id_id
                            v_list.append(input_val)
                        value_list.append(v_list)

                    else:
                        v_list = []
                        value_list.append(v_list)

                # item[choice_id] = choice_con
                # self.save_id_con(item)
                c_list.append(item)
                item_list.append(choice_id)
                item_list_txt.append(choice_con)
        if choice_flag == 0:
            message = {
                'iw': iw,
                'id_question': data_qid,
                'id_question_txt': data_con,
                'items': item_list,
                'items_txt': item_list_txt
            }
        else:
            message = {
                'iw': iw,
                'id_question': data_qid,
                'id_question_txt': data_con,
                'items': item_list,
                'items_txt': item_list_txt,
                'values': value_list
            }
        return message

    def blank_fill(self, iw, data_qid, response, data_con):
        """
        填入信息: 时间 地点 普通文本(金额,原因etc)
        :return:
        """
        str_res = etree.HTML(response)
        lp_input = str_res.xpath('//div[@class="mpage"]//div[@class="questoin_more_options lp_input"]')
        c_list = []
        item_list = []
        item_list_txt = []
        value_list = []
        tip_list = []
        for lp in lp_input:
            item = {}
            lp_con = lp.xpath('./div[@class="weui_cells_title"]/text()')[0].strip()
            lp_tip = lp.xpath('./div[@class="weui_cells_tip"]/text()')
            try:
                tip = lp.xpath('./div[@class="weui_cells_title"]/span/text()')[0].strip()
            except:
                # 没有选填
                tip = ''
            # tip = ''
            if len(lp_tip) > 0:
                lp_con = ' '.join([lp_con, lp_tip[0].strip()])
            lp_id = lp.xpath('./div[@class="weui_cells_title"]/@id')[0]
            try:
                lp_id = lp_id.split('_')[-1]
            except Exception as e:
                print('lp_id not find:', e)
            else:
                if len(tip) > 0:
                    tip_tip = '1'
                else:
                    tip_tip = '0'
                tip_list.append(tip_tip)
                item[lp_id] = lp_con
                # self.save_id_con(item)
                c_list.append(item)
                item_list.append(lp_id)
                item_list_txt.append(lp_con)
        for i in range(len(c_list)):
            c = c_list[i]
            v_list = []
            if tip_list[i] == '0':
                post_id = tuple(c.keys())[0]
                post_con = tuple(c.values())[0]
                re_area = post_id + '" data-it="103"'
                area_find = re.findall(re_area, response)
                if area_find != []:
                    # 存在地区填空
                    input_val = self.choice_area()
                    v_list.append(input_val)

                re_money = post_id + '" data-it="5"'
                money_find = re.findall(re_money, response)
                if money_find != []:
                    # 存在金额填空
                    input_val = self.choice_money()
                    v_list.append(input_val)

                re_date = post_id + '" data-it="3"'
                date_find = re.findall(re_date, response)
                if date_find != []:
                    # 存在时间填空
                    input_val = self.choice_date()
                    v_list.append(input_val)

                re_age = post_id + '" data-it="4"'
                age_find = re.findall(re_age, response)
                if age_find != []:
                    # 存在年龄填空
                    input_val = self.choice_age()
                    v_list.append(input_val)

                re_tian = post_id + '" data-it="9"'
                tian_find = re.findall(re_tian, response)
                if tian_find != []:
                    # 存在天数填空
                    print('here====')
                    input_val = self.choice_tian()
                    v_list.append(input_val)

                re_space = post_id + '" data-it="6"'
                space_find = re.findall(re_space, response)
                if space_find != []:
                    # 存在面积填空
                    input_val = self.choice_space()
                    v_list.append(input_val)

                re_yue = post_id + '" data-it="12"'
                yue_find = re.findall(re_yue, response)
                if yue_find != []:
                    # 存在月份填空
                    input_val = self.choice_space()
                    v_list.append(input_val)

                page_silder = 'id_item_slider_{post_id}'.format(post_id=post_id)
                silder_input = re.findall(page_silder, response)
                if silder_input != []:
                    # 存在普通选择
                    id_silder = '//div[@id="id_item_slider_{post_id}"]'.format(post_id=post_id)
                    p_list_xpath = id_silder + '//p[@data-is_parent="0"]'
                    p_list = str_res.xpath('{p_list_xpath}'.format(p_list_xpath=p_list_xpath))
                    if len(p_list) > 0:
                        for p in p_list:
                            item = {}
                            data_id = p.xpath('./@data-id')[0]
                            data_w_con = p.xpath('./text()')[0]
                            if data_w_con == '澳门特别行政区':
                                pass
                            else:
                                # item[data_id] = data_w_con
                                # self.save_id_con(item)
                                c[data_id] = data_w_con
                                input_val = data_id
                                v_list.append(input_val)

                text_re = post_id + '" type="text"'
                text_find = re.findall(text_re, response)
                if text_find != []:
                    # 存在填空
                    input_val = '金明'

                value_list.append(v_list)
            else:
                post_id = tuple(c.keys())[0]
                post_con = tuple(c.values())[0]
                re_date = post_id + '" data-it="3"'
                date_find = re.findall(re_date, response)
                if date_find != []:
                    # 存在时间填空
                    input_val = self.choice_date()
                    v_list.append(input_val)
                else:
                    input_val = ''
                    v_list.append(input_val)
                value_list.append(v_list)
        message = {
            'iw': iw,
            'id_question': data_qid,
            'id_question_txt': data_con,
            'items': item_list,
            'items_txt': item_list_txt,
            'values': value_list
        }
        return message

    def blank_input(self, iw, data_qid, response, data_con):
        """
        文本框
        :param response:
        :return: 表单提交 item[]: 参数 input_val_参数: 文本 action: next
        """
        # print(data_con)
        str_res = etree.HTML(response)
        text_input = str_res.xpath('//div[@class="mpage"]//textarea[@class="weui_input input_val"]')
        c_list = []
        item_list = []
        item_list_txt = []
        value_list = []
        if text_input != []:
            for text in text_input:
                v_list = []
                item = {}
                text_con = data_con
                text_id = text.xpath('./@id')[0]
                try:
                    text_id = text_id.split('_')[-1]
                except Exception as e:
                    print('text_id not find:', e)
                else:
                    item_list.append(text_id)
                    item_list_txt.append(text_con)
                    item[text_id] = text_con
                    self.save_id_con(item)
                input_val = '我想问这种情况是不是'
                v_list.append(input_val)
                value_list.append(v_list)
        else:

            re_area = '"id_input_val_(.*?)" data-it="103"'
            area_find = re.findall(re_area, response)
            # item_list.append(area_find[0])
            item_list.append(data_qid)
            item_list_txt.append(data_con)
            v_list = []
            if area_find != []:
                # 存在地区填空
                input_val = self.choice_area()
                v_list.append(input_val)
                value_list.append(v_list)

            re_date = '"id_input_val_(.*?)" data-it="3"'
            date_find = re.findall(re_date, response)
            if date_find != []:
                # 存在时间填空
                input_val = self.choice_date()
                v_list.append(input_val)
                value_list.append(v_list)

            re_money = '"id_input_val_(.*?)" data-it="5"'
            money_find = re.findall(re_money, response)
            if money_find != []:
                # 存在金额填空
                input_val = self.choice_money()
                v_list.append(input_val)
                value_list.append(v_list)

            re_age = '"id_input_val_(.*?)" data-it="4"'
            age_find = re.findall(re_age, response)
            if age_find != []:
                # 存在年龄填空
                input_val = self.choice_age()
                v_list.append(input_val)
                value_list.append(v_list)

            text_month = '几个月'
            re_number = 'name="input_val_' + data_qid + '" type="number"'
            if text_month in data_con and re_number in response:
                # 存在月份填空
                input_val = '3'
                v_list.append(input_val)
                value_list.append(v_list)

            text_txt = '在哪'
            re_number = 'name="input_val_' + data_qid + '" type="text"'
            if text_txt in data_con and re_number in response:
                # 存在地点填空
                input_val = '地址'
                v_list.append(input_val)
                value_list.append(v_list)

        message = {
            'iw': iw,
            'id_question': data_qid,
            'id_question_txt': data_con,
            'items': item_list,
            'items_txt': item_list_txt,
            'values': value_list
        }
        # print('message', message)
        return message

    def choice_area(self):  # 地区
        return '132'  # 北京市东城区

    def choice_age(self):  # 年龄
        return '18'  # 默认年龄 18

    def choice_tian(self):
        return '30'  # 天数

    def choice_space(self):
        return '120'  # 面积 120平方

    def choice_tel(self):  # 电话
        return '13968606875'

    def choice_sex(self):
        # data-it="257"
        return '3888'  # 女

    def choice_date(self):  # 日期
        return '2018-05-01'  # 9-18岁

    def choice_money(self):
        return '5000'  # 默认金额

    def choice_nation(self):
        return '3889'  # 汉族

    def docx_download(self, down_id):
        down_url = 'https://ai.12348.gov.cn/g/r/report/download/?id={down_id}'.format(down_id=down_id)
        headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Mobile Safari/537.36'
        }
        # file_name = ''.join([down_id, '.docx'])
        res = requests.get(down_url, headers=headers)
        file_name = ''.join(['./files/', down_id, '.docx'])
        with open(file_name, 'wb') as f:
            f.write(res.content)
        # urlretrieve(down_url, file_name)
        print(down_id, '下载完毕!')

    def html_download(self, down_id):
        down_url = "https://ai.12348.gov.cn/g/r/c/{type_sort}?id={down_id}&device_type=1".format(type_sort=TYPE_SOFT,
                                                                                                 down_id=down_id)
        headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Mobile Safari/537.36'
        }
        file_path = FILEPATH_DOWN + TYPE_SOFT
        if not os.path.exists(file_path):
            os.mkdir(file_path)
        response = requests.get(down_url, headers=headers)
        html = response.content.decode()
        file_name = ''.join([file_path, '/', down_id, '.html'])
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(html)
        print(down_id, '下载完毕!')

    def save_id_con(self, item):
        client = MongoClient(
            host=conf.MONGDB_HOST,
            port=conf.PORT
        )
        db = client[conf.MONGODB_DBNAME]
        collection = db[conf.MONGODB_COL_AL]
        collection.insert(item)

    def process_results(self, response):
        try:
            html_content = response['c']
            iw = response['iw']
        except Exception as e:
            print('报错', e)
            print(response)
            message = {}
            message['iw'] = -1
        else:
            if 'url' not in response:
                message = self.question_page(html_content, iw)
                return message
            else:
                message = {}
                message['iw'] = 99
                report_id = response['url'].split('&')[0].split('?id=')[-1]
                message['report'] = report_id
                self.html_download(down_id=report_id)
                return message

    def process_message(self, iw, message):
        response = ''
        if iw == 4:
            form_data = {
                'item': message['items'][0],
                'action': 'next'
            }
            response = self.parse_post_url(cookie, form_data)
        if iw == 1:
            if 'values' in message.keys():
                input_val = 'input_val_' + message['items'][0]
                form_data = {
                    'item': message['items'][0],
                    'action': 'next'
                }
                if message['values'][0] != []:
                    form_data[input_val] = message['values'][0][0]
                else:
                    form_data = {
                          'item': message['items'][0],
                        'action': 'next'
                    }
            else:
                form_data = {
                    'item': message['items'][0],
                    'action': 'next'
                }
            response = self.parse_post_url(cookie, form_data)
            print(form_data)
        if iw == 2:
            if 'values' in message.keys():
                input_val = 'input_val_' + message['items'][0]
                form_data = {
                    'item[]': message['items'][0],
                    'action': 'next'
                }
                if message['values'][0] != []:
                    form_data[input_val] = message['values'][0][0]
                else:
                    form_data = {
                        'item[]': message['items'][0],
                        'action': 'next'
                    }
            else:
                form_data = {
                    'item[]': message['items'][0],
                    'action': 'next'
                }
            response = self.parse_post_url(cookie, form_data)
        if iw == 3:
            # print('======', message)
            input_val = 'input_val_' + message['items'][0]
            form_data = {
                'item': message['items'][0],
                'action': 'next'
            }
            form_data[input_val] = message['values'][0][0]
            response = self.parse_post_url(cookie, form_data)
        if iw == 5:
            items = message['items']
            input_item = []
            input_val_list = []
            form_data = {}
            for i in range(len(items)):
                input_val = 'input_val_' + message['items'][i]
                input_item.append(message['items'][i])
                if message['values'][i] == []:
                    form_data[input_val] = ''
                else:
                    form_data[input_val] = message['values'][i][0]
            form_data['action'] = 'next'
            form_data['item[]'] = input_item
            response = self.parse_post_url(cookie, form_data)
        return response


if __name__ == '__main__':
    flag = FLAG
    ai_12348 = SpiderAi12348()
    cookie = conf.get_session()
    response, cookie = ai_12348.parse_url(cookie)
    if flag:
        tree = Tree(FILENAME)
        html_content = response['c']
        iw = response['iw']
        message = ai_12348.question_page(html_content, iw)
    else:
        tree = Tree(FILENAME, follow_pre=True)
        path = tree.next_path()
        print('==========', path)

    while True:
        if flag:
            path = tree.construct(message)
            print(path)
        while not path:
            message = ai_12348.process_results(response)
            print('此时的message:', message)
            iw = message['iw']
            response = ai_12348.process_message(iw, message)
            message_pro = ai_12348.process_results(response)
            path = tree.construct(message_pro)
            print('新的path', path)
        tree = Tree(FILENAME, follow_pre=True)
        if not tree.curnode:
            break
        cookie = conf.get_session()
        response, cookie = ai_12348.parse_url(cookie)
        html_content = response['c']

        for i in path:
            print('&&&', i)
            iw = i['iw']
            if iw == 4:
                form_data = {
                    'item': i['item'][0],
                    'action': 'next'
                }
                response = ai_12348.parse_post_url(cookie, form_data)
            if iw == 1:
                if 'value' in i.keys():
                    if i['value'][0] != []:
                        input_val = 'input_val_' + i['item'][0]
                        form_data = {
                            'item': i['item'][0],
                            'action': 'next'
                        }
                        form_data[input_val] = i['value'][0]
                    else:
                        form_data = {
                            'item': i['item'][0],
                            'action': 'next'
                        }
                else:
                    form_data = {
                        'item': i['item'][0],
                        'action': 'next'
                    }
                response = ai_12348.parse_post_url(cookie, form_data)
            if iw == 2:
                if 'value' in i.keys():
                    if i['value'][0] != []:
                        input_val = 'input_val_' + i['item'][0]
                        form_data = {
                            'item[]': i['item'][0],
                            'action': 'next'
                        }
                        form_data[input_val] = i['value'][0]
                    else:
                        form_data = {
                            'item[]': i['item'][0],
                            'action': 'next'
                        }
                else:
                    form_data = {
                        'item[]': i['item'][0],
                        'action': 'next'
                    }
                response = ai_12348.parse_post_url(cookie, form_data)
            if iw == 3:
                input_val = 'input_val_' + i['item'][0]
                form_data = {
                    'item': i['item'][0],
                    'action': 'next'
                }
                form_data[input_val] = i['value'][0]
                response = ai_12348.parse_post_url(cookie, form_data)
            if iw == 5:
                input_item = []
                input_val_list = []
                form_data = {}
                for m in range(len(i['item'])):
                    input_val = 'input_val_' + i['item'][m]
                    input_item.append(i['item'][m])
                    form_data[input_val] = i['value'][m]
                form_data['action'] = 'next'
                form_data['item[]'] = input_item
                try:
                    response = ai_12348.parse_post_url(cookie, form_data)
                except Exception as e:
                    print('e')
            message = ai_12348.process_results(response)
            flag = True
