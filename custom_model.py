#!/usr/bin/env python
# -*- coding: utf-8 -*-

from peewee import *


class settings:
    version = "1"
    db_name = "postgres"
    user = "ken"
    password = "hh87z6r30"
    host = "127.0.0.1"


class Org(Model):
    name = TextField()
    create_time = DateTimeField()


class User(Model):
    name = TextField()
    email = TextField(unique=True)
    age = IntegerField(null=True)
    org = ForeignKeyField(Org, related_name='users')
