#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib
import re
import json
import tornado
from common import *
from tornado.web import RequestHandler
from peewee import PostgresqlDatabase
from peewee import Model
from peewee import ForeignKeyField


def getAllModel(model_path):
    model_module = importlib.import_module(model_path)
    models = {}
    for attr_name in dir(model_module):
        attr = getattr(model_module, attr_name)
        try:
            if issubclass(attr, Model) and attr.__name__ != 'Model':
                attr._meta.database = db
                models[attr.__name__.lower()] = attr
        except Exception:
            continue
    return models


def parseResource(models):
    route_map = {}
    for model_name in models:
        model = models.get(model_name)
        regexps = route_map.get(model.__name__.lower())
        if not regexps:
            regexps = []
            route_map[model.__name__.lower()] = regexps
        regexps.append("(.*)")
        for prop_name in dir(model):
            prop = getattr(model, prop_name)
            try:
                if isinstance(prop, ForeignKeyField):
                    fk_regexps = route_map[prop_name]
                    if not fk_regexps:
                        fk_regexps = []
                        route_map[model.__name__.lower()] = fk_regexps
                    fk_regexps.append("(.*)/%s" % model.__name__.lower())
                    fk_regexps.append("(.*)/%s/(.*)" % model.__name__.lower())
            except Exception:
                continue
    for model_name in route_map:
        route_map[model_name] = sorted(route_map[model_name], key=len, reverse=True)
    return route_map


def parseURI(uri):
    p = re.compile("([\w*\d*]+)[/]?([\w*\d*]*)")
    return p.findall(uri)


class rest(RequestHandler):

    def initialize(self):
        print self.settings
        self.db = db
        self.model_path = self.settings.get("model_path")
        self.models = getAllModel(self.model_path)

    @handleError
    def get(self, parm_str=""):
        parms = parseURI(self.request.uri)
        records = []
        if not parms:
            raise Exception("访问根路径失败")
        sql_query = None
        for parm in parms:
            model_name = parm[0]
            id = parm[1]
            model = self.models.get(model_name)
            if not sql_query:
                sql_query = model.select(self.models.get(parms[-1][0]))
            else:
                sql_query = sql_query.join(model)
            if id:
                sql_query = sql_query.where(model.id == id)
        records = list(sql_query.dicts().execute())
        self.write(json.dumps({"error": "0", "result": records}, cls=ExtEncoder))

    @handleError
    def post(self, parm_str=""):
        parms = parseURI(self.request.uri)
        if not parms:
            raise Exception("访问根路径失败")
        model = self.models.get(parms[0][0])
        model.insert(**self.arguments)
        self.write(json.dumps({"error": "0"}))

    @handleError
    def put(self, parm_str=""):
        parms = parseURI(self.request.uri)
        if not parms:
            raise Exception("访问根路径失败")
        model = self.models.get(parms[0][0])
        model.update(**self.arguments).where(model.id == parms[0][1])

    @handleError
    def delete(self, parm_str=""):
        parms = parseURI(self.request.uri)
        if not parms:
            raise Exception("访问根路径失败")
        model = self.models.get(parms[0][0])
        model.delete().where(model.id == parms[0][1])


if __name__ == '__main__':
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        # 为了方便调试，先改成9000端口启动
        port = 9000
    print port

    url_map = []
    url_map.append((r'/', rest))
    url_map.append((r'/(.*)', rest))

    db_name = "postgres"
    user = "ken"
    password = "hh87z6r30"

    db = PostgresqlDatabase(db_name, user=user, password=password, host='127.0.0.1')

    settings = {
        'debug': True,
        'cookie_secret': 'tornado rest',
        'db': db,
        'model_path': 'custom_model'
    }

    application = tornado.web.Application(url_map, **settings)
    application.listen(port)
    ioloop = tornado.ioloop.IOLoop().instance()
    tornado.autoreload.start(ioloop)
    ioloop.start()
