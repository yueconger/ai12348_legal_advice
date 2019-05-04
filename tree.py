# -*- coding: utf-8 -*-


import shutil
from itertools import product

from pyquery import PyQuery as pq


class Tree(object):
    # template
    # <node iw="" id_question="" item="" value="" flag=""></node>
    node = pq('<node></node>')
    report = pq('<report iw="99"></report>')

    def __init__(self, filename, follow_pre=False):
        self.filename = filename
        if not (shutil.os.path.exists(filename) or follow_pre):
            open(filename, 'w', encoding='utf8').write('')
        if not follow_pre:
            self.root = pq('<root></root>')
            self.curnode = self.root  # initial node is root node
        else:
            self.root = pq(open(filename, 'rb').read())
            self.curnode = self.root('[flag=undo]').eq(0)

    def generate_node(self, iw, id_question=None, id_question_txt=None, items=None, items_txt=None, values=None):
        '''generate nodes and vary according to inputs
        :param iw: 数据类型
        :param id_question: 页面id
        :param items: item或item_title的id
        :param values: item_titel对应的item_value'''
        if iw in [1, 2, 4] and values:
            for item, item_txt, value in zip(items, items_txt, values):
                n = self.node.clone()
                if not value:
                    n.attr('iw', str(iw))
                    n.attr('id_question', id_question)
                    n.attr('id_question_txt', id_question_txt)
                    n.attr('item', item)
                    n.attr('item_txt', item_txt)
                    n.attr('flag', 'undo')
                    yield n
                else:
                    for val in value:
                        n = self.node.clone()
                        n.attr('iw', str(iw))
                        n.attr('id_question', id_question)
                        n.attr('id_question_txt', id_question_txt)
                        n.attr('item', item)
                        n.attr('item_txt', item_txt)
                        n.attr('value', val)
                        n.attr('flag', 'undo')
                        yield n
        elif iw in [1, 2, 4]:  # 单选/多选（当作单选）
            for item, item_txt in zip(items, items_txt):
                n = self.node.clone()
                n.attr('iw', str(iw))
                n.attr('id_question', id_question)
                n.attr('id_question_txt', str(id_question_txt))
                n.attr('item', item)
                n.attr('item_txt', item_txt)
                n.attr('flag', 'undo')
                yield n
        elif iw == 3 or iw == 5:  # input area or inputs
            values = list(product(*values))
            for value in values:
                n = self.node.clone()
                n.attr('iw', str(iw))
                n.attr('id_question', id_question)
                n.attr('id_question_txt', id_question_txt)
                n.attr('item', '||'.join(items))
                n.attr('item_txt', '||'.join(items_txt))
                n.attr('value', '||'.join(value))
                n.attr('flag', 'undo')
                yield n
        elif iw == -1:  # fail
            n = self.node.clone()
            n.attr('flag', 'fail')
            yield n

    def add_node(self, iw, id_question=None, id_question_txt=None, items=None, items_txt=None, values=None):
        '''add child nodes
        当前节点为根节点或第一个有`undo`flag的节点时，当前节点不变，否则为子节点中第一个
        将当前节点flag标记为`done`，并增加子节点
        '''
        if self.curnode.children('node').eq(0):
            self.curnode = self.curnode.children('node').eq(0)
        if not self.curnode.is_('root'):
            self.curnode.attr('flag', 'done')
        for n in self.generate_node(iw, id_question, id_question_txt, items, items_txt, values):
            self.curnode.append(n)

    def add_report(self, report):
        '''add child node -- report'''
        if self.curnode.children('node').eq(0):
            self.curnode = self.curnode.children('node').eq(0)
        if not self.curnode.is_('root'):
            self.curnode.attr('flag', 'done')
        rp = self.report.clone()
        rp.text(report)
        self.curnode.append(rp)

    def next_path(self):
        '''return next path'''
        ele = self.root('[flag=undo]').eq(0)
        if not ele:  # no node with flag equals to "undo"
            print('all done')
            return
        path = []
        for i, ele_ in enumerate(ele.parents().items()):
            if i == 0:  # first element in parents is root node
                continue
            data = {
                'iw': int(ele_.attr('iw')),
                'id_question': ele_.attr('id_question')}
            if ele_.attr('item'):
                data['item'] = ele_.attr('item').split('||')
            if ele_.attr('value'):
                data['value'] = ele_.attr('value').split('||')
            path.append(data)
        data = {
            'iw': int(ele.attr('iw')),
            'id_question': ele.attr('id_question')}
        if ele.attr('item'):
            data['item'] = ele.attr('item').split('||')
        if ele.attr('value'):
            data['value'] = ele.attr('value').split('||')
        path.append(data)
        return path

    def construct(self, message):
        '''
        message = {
            'iw': [1, 2, 3, 4, 5, -1, 99],
            'id_question': id_question,
            'items': [id1, id, ...],
            'values': [[id1_val1], [id2_val1, ...], ...]}
        '''
        iw = message['iw']
        if iw == 99:
            report = message.get('report')
            self.add_report(report)
            self.save()
            print('report saved')
            return self.next_path()
        elif iw == -1:
            self.add_node(iw)
            self.save()
            print('this path is failed!')
            return self.next_path()
        elif iw in [1, 2, 4]:
            id_question_txt = message.get('id_question_txt')
            items_txt = message.get('items_txt')
            id_question = message.get('id_question')
            items = message.get('items')
            values = message.get('values')
            self.add_node(iw, id_question, id_question_txt, items, items_txt, values)
            print('add node successed')
            return
        elif iw in [3, 5]:
            id_question_txt = message.get('id_question_txt')
            items_txt = message.get('items_txt')
            id_question = message.get('id_question')
            items = message.get('items')
            values = message.get('values')
            self.add_node(iw, id_question, id_question_txt, items, items_txt, values)
            print('add node successed')
            return

    def save(self):
        if shutil.os.path.exists(self.filename):
            shutil.copy(self.filename, self.filename + '.bak')
        with open(self.filename, 'w', encoding='utf8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(self.root.outer_html() + '\n')


if __name__ == '__main__':
    # curnode = root
    pass
