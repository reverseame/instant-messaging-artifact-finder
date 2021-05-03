from datetime import datetime


def dictionary_representation(obj):
    """Returns a dictionary that represents the object supplied as an argument"""
    if isinstance(obj, datetime):
        return dict(year=obj.year, month=obj.month, day=obj.day, hour=obj.hour, minute=obj.minute, second=obj.second)
    else:
        return obj.__dict__
