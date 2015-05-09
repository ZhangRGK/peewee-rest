#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import time
import decimal
import utils
import functools
import json
import sys
import traceback


def handleError(method):
    '''
    出现错误的时候,用json返回错误信息回去
    很好用的一个装饰器
    '''
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            method(self, *args, **kwargs)
        except Exception:
            self.write(json.dumps({'error': getExpInfoAll(True)}))
            print getExpInfoAll()
    return wrapper


class ExtEncoder(json.JSONEncoder):

    '''
    modify by bigzhu at 15/01/30 11:25:22 增加对 utils.IterBetter 的支持
    '''

    def default(self, o):
        if isinstance(o, datetime.datetime) or isinstance(o, datetime.date):
            return time.mktime(o.timetuple()) * 1000
        elif isinstance(o, decimal.Decimal):
            return float(o)
        elif isinstance(o, utils.IterBetter):
            return list(o)
        # Defer to the superclass method
        return json.JSONEncoder(self, o)


def getExpInfoAll(just_info=False):
    '''得到Exception的异常'''
    if just_info:
        info = sys.exc_info()
        return str(info[1])
    else:
        return traceback.format_exc()
