from datetime import datetime
import json


def dictionary_representation(obj):
    """Returns a dictionary that represents the object supplied as an argument"""
    if isinstance(obj, datetime):
        return dict(year=obj.year, month=obj.month, day=obj.day, hour=obj.hour, minute=obj.minute, second=obj.second)
    else:
        return obj.__dict__


def json_representation(obj) -> str:
    """Returns the JSON representation of an object"""
    return json.dumps(obj, ensure_ascii=False, indent=4, default=dictionary_representation)
