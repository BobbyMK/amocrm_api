# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import copy
from datetime import datetime
from collections import namedtuple, OrderedDict

from .decorators import lazy_dict_property

class Empty(object):
    pass


class BaseField(object):
    _parent = None

    def __init__(self, field=None, *args, **kwargs):
        self.field = field
        self._data = {}
        self._args, self._kwargs = args, kwargs

    def __get__(self, obj, _=None):
        if not self._data:
            if self._parent:
                self.data = obj.data.get(self._parent, {}).get(self.field)
            else:
                self.data = obj.data.get(self.field)
            if hasattr(self, 'keys_map'):
                self._keys_data = {key: obj.data.get(val) for key, val in self.keys_map.items()}
        return self.data

    # def __set__(self, value):
        # self.set_data(value)
    def __copy__(self):
        # We need to avoid hitting __reduce__, so define this
        # slightly weird copy construct.
        obj = Empty()
        obj.__class__ = self.__class__
        obj.__dict__ = self.__dict__.copy()
        return obj

    def cleaned_data(self):
        return self._data

    def set_data(self, value):
        self._data = value
        return self

    @property
    def data(self):
        return self.cleaned_data()

    @data.setter
    def data(self, value):
        self.set_data(value)


class Field(BaseField):
    pass


class ConstantField(BaseField):

    def __init__(self, field=None, value=None):
        super(ConstantField, self).__init__(field)
        self._data = value


class DateTimeField(Field):

    def cleaned_data(self):
        return datetime.fromtimestamp(super(DateTimeField, self).cleaned_data())


class BooleanField(Field):

    def cleaned_data(self):
        data = super(BooleanField, self).cleaned_data()
        data = int(data) if str(data).isdigit() else data
        return bool(data)


class ForeignField(Field):

    def __init__(self, object_type=None, field=None, keys=None):
        super(ForeignField, self).__init__(field)
        self._keys, self._keys_data = keys, {}
        self.object_type = object_type

    @property
    def _keys_map(self):
        if isinstance(self._keys, (list, tuple)):
            return dict(zip(self._keys))
        elif isinstance(self._keys, dict):
            return self._keys
        return {}

    def cleaned_data(self):
        _id = super(ForeignField, self).cleaned_data()
        wrap = lambda this: this.get(_id)
        obj = lazy_dict_property(wrap).__get__(self.object_type.objects)
        [setattr(obj, name, value) for name, value in self._keys_data.items()]
        return obj


class ManyForeignField(Field):

    def __init__(self, objects_type=None, field=None, key=None):
        super(ManyForeignField, self).__init__(field)
        self.objects_type = objects_type
        self.key = key

    def cleaned_data(self):
        data = super(ManyForeignField, self).cleaned_data()
        items = []
        for item in data:
            wrap = lambda this: this.get(item)
            item = lazy_dict_property(wrap).__get__(self.objects_type.objects)
            items.append(item)
        return items


class ManyDictField(Field):

    def __init__(self, field=None, key=None):
        super(ManyDictField, self).__init__(field)
        self.key = key
    
    def cleaned_data(self):
        data = super(ManyDictField, self).cleaned_data()
        _items = namedtuple('items', [i.get(self.key, 'pass') for i in data])
        items = {}
        for item in data:
            item = OrderedDict(item)
            _item = namedtuple('item', item.keys())
            items[item[self.key]] = _item(**item)
        return _items(**items)


class CustomField(Field):
    _parent = 'custom_fields'