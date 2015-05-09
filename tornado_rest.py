#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib
import re
import json
from common import *
from tornado.web import RequestHandler
from peewee import PostgresqlDatabase
from peewee import Model
from peewee import ForeignKeyField

db_name = "postgres"
user = "ken"
password = "hh87z6r30"

db = PostgresqlDatabase(db_name, user=user, password=password, host='127.0.0.1')


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


class RestHandler(RequestHandler):

    def initialize(self):
        self.db = db
        self.model_path = self.setting["model_path"]
        self.models = getAllModel(self.model_path)
        # self.reg = parseResource(self.models)

    @handleError
    def get(self):
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
                sql_query = model.select(models.get(parms[-1][0]))
            else:
                sql_query = sql_query.join(model)
            if id:
                sql_query = sql_query.where(model.id == record_id)
        records = list(sql_query.dicts().execute())
        self.write(json.dumps({"error": "0", "result": records}, cls=ExtEncoder))

    @handleError
    def post(self):
        parms = parseURI(self.request.uri)
        if not parms:
            raise Exception("访问根路径失败")
        model = self.models.get(parms[0][0])
        model.insert(**self.arguments)
        self.write(json.dumps({"error": "0"}))

    @handleError
    def put(self):
        parms = parseURI(self.request.uri)
        if not parms:
            raise Exception("访问根路径失败")
        model = self.models.get(parms[0][0])
        model.update(**self.arguments).where(model.id == parms[0][1])

    @handleError
    def delete(self):
        parms = parseURI(self.request.uri)
        if not parms:
            raise Exception("访问根路径失败")
        model = self.models.get(parms[0][0])
        model.delete().where(model.id == parms[0][1])


if __name__ == '__main__':
    models = getAllModel("custom_model")
    uri = "/org/1/user/2"
    parms = parseURI(uri)
    print parms
    sql_query = None
    for parm in parms:
        model_name = parm[0]
        record_id = parm[1]
        model = models.get(model_name)
        if not sql_query:
            sql_query = model.select()
        else:
            sql_query = sql_query.join(model)
        if record_id:
            sql_query = sql_query.where(model.id == record_id)
    # Org = models["org"]
    # User = models["user"]
    # sql_query = Org.select().where(Org.id == 2).join(User).where(User.id == 1)
    print list(sql_query.dicts().execute())
    # records = sql_query.dicts().sql()
