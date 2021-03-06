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


def getAllModel(model_module):
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
    return p.findall(re.sub("/api/v\d+", "", uri))


class RestHandler(RequestHandler):

    def initialize(self, model_module, db):
        self.db = db
        self.models = getAllModel(model_module)

    @handleError
    def get(self, parm_str=""):
        parms = parseURI(self.request.uri)
        records = []
        if not parms:
            # self.set_status()
            raise Exception("访问根路径失败")
        sql_query = None
        for parm in parms:
            model_name = parm[0]
            id = parm[1]
            print model_name
            print self.models
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
    model_path = 'custom_model'
    model_module = importlib.import_module(model_path)

    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        port = 9000
    print port

    db = PostgresqlDatabase(model_module.settings.db_name, user=model_module.settings.user, password=model_module.settings.password, host=model_module.settings.host)

    url_map = []
    url_map.append((r'/api/v%s' % model_module.settings.version, RestHandler, dict(model_module=model_module, db=db)))
    url_map.append((r'/api/v%s(.*)' % model_module.settings.version, RestHandler, dict(model_module=model_module, db=db)))

    settings = {
        'debug': True,
        'cookie_secret': 'tornado rest',
        'model_path': model_path
    }

    application = tornado.web.Application(url_map, **settings)
    application.listen(port)
    ioloop = tornado.ioloop.IOLoop().instance()
    tornado.autoreload.start(ioloop)
    ioloop.start()
