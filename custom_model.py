#!/usr/bin/env python
# -*- coding: utf-8 -*-

from peewee import *

__version__ = "1"


class Org(Model):
    name = TextField()
    create_time = DateTimeField()


class User(Model):
    name = TextField()
    email = TextField(unique=True)
    age = IntegerField(null=True)
    org = ForeignKeyField(Org, related_name='users')
