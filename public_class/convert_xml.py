# -*- coding:UTF-8 -*-
"""xml对象转换类
使用方法：
1. 所有对象类必须继承Basic类，并且实现__init__方法，且都具有__name__全局属性
2. xml节点名称由__name__确定，并不由类名确定
3. 所有对象类属性值如果具有xml属性，必须通过set_param函数赋值

例如：
class Response(Basic):
    __name__ = 'response'
    def __init__(self):
        pass
"""
import xml.dom.minidom
__author__ = 'yangming'


def set_param(values=None, types='text', **kwargs):
    """
    设置参数，例如：p = set_param(100, types='cdata', name='ym')
    :param values: 对象属性值
    :param types: 对象属性类型
    :param kwargs: 对象对应的dom节点属性值
    :return:
    """
    if values is None or isinstance(values, dict):
        kwargs = dict()
    else:
        kwargs['values'] = values
        kwargs['types'] = types
    return kwargs


class Basic(object):
    __name__ = 'Basic'

    def __set_params__(self):
        """
        设置对象所有属性值
        """
        for attr in self.__dict__.keys():
            param = self.__getattribute__(attr)
            if param is not None and not isinstance(param, dict):
                if isinstance(param, list):
                    params = list()
                    for p in param:
                        params.append(set_param(p))
                    self.__setattr__(attr, set_param(params))
                else:
                    self.__setattr__(attr, set_param(param))

            '''
            # self.__setattr__(attr, dict(types='cdata', value=values))
            self.__getattribute__(attr)['types'] = 'cdata' if cdata else 'text'
            self.__getattribute__(attr)['value'] = values
            '''


class TestResponse(Basic):
    __name__ = 'testResponse'

    def __init__(self):
        self.name = None
        self.age = None


class ConvertXML(object):
    """
    转换xml字符串为python对象或转换python对象为xml字符串
    """
    def __init__(self, base_obj=None):
        self.base_obj = base_obj
        self.impl = xml.dom.minidom.getDOMImplementation()
        self.dom = self.impl.createDocument(None, self.base_obj.__name__, None)
        self.root = self.dom.documentElement

    @staticmethod
    def _set_attr(dom, values):
        """
        设置dom属性
        :param dom: dom对象
        :param values: 属性值，例如：{'name': 'python', ...}
        :return:
        """
        for attr_key, attr_val in values.iteritems():
            if attr_key not in ('values', 'types'):
                dom.setAttribute(attr_key, str(attr_val))

    def _attr_to_xml(self, key, values):
        """
        将对象属性转化成xml的dom对象
        :param key: 对象属性名称
        :param values: 对象属性值
        :return:
        """
        key_dom = self.dom.createElement(key)
        types = values.get('types')
        value = values.get('values')
        if not isinstance(value, str) and not isinstance(value, unicode):
            value = str(value)

        # 设置dom节点属性
        ConvertXML._set_attr(key_dom, values)

        # 设置节点数据类型及值
        if types == 'text':
            val_dom = self.dom.createTextNode(value)
        elif types == 'cdata':
            val_dom = self.dom.createCDATASection(value)
        else:
            val_dom = 'null'
        key_dom.appendChild(val_dom)
        return key_dom

    def _class_to_xml(self, key, values=None):
        """
        将类转换成xml的dom对象
        :param key: 类对象属性名称或类名称
        :param values: 类对象属性值或类对象，类型必须是字典
        :return:
        """
        if isinstance(values, dict):
            value = values.get('values')
        else:
            value = None

        if value is None:
            return self.dom.createElement(key)

        if isinstance(value, list):
            # 列表中只能包含对象
            item = self.dom.createElement(key)
            for o in value:
                ConvertXML._set_attr(item, values)
                item.appendChild(self._class_to_xml(None, o))
        elif isinstance(value, Basic):
            value.__set_params__()
            keys = value.__dict__.keys()
            item = self.dom.createElement(value.__name__)

            ConvertXML._set_attr(item, values)

            for cls_key in keys:
                cls_val = getattr(value, cls_key)
                item.appendChild(self._class_to_xml(cls_key, cls_val))
        else:
            item = self._attr_to_xml(key, values)

        return item

    def parse_xml(self, s=None):
        pass

    def toxml(self):
        """
        将Basic类型对象转换成xml字符串
        :return:
        """
        if self.base_obj is None:
            return ''

        if not isinstance(self.base_obj, Basic):
            return ''

        self.base_obj.__set_params__()
        keys = self.base_obj.__dict__.keys()
        if len(keys) == 0:
            return ''

        for key in keys:
            value = getattr(self.base_obj, key)
            try:
                sub_dom = self._class_to_xml(key, value)
            except Exception as ex:
                sub_dom = None
                print(ex.message)
            finally:
                self.root.appendChild(sub_dom)

        return self.dom.toxml()

if __name__ == '__main__':
    t = TestResponse()
    t.test_name = set_param('convert_xml', types='cdata', id=1)
    t.age = '15'

    cx = ConvertXML(t)
    print(cx.toxml())
