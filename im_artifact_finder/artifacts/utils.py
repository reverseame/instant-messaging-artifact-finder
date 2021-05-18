import datetime
import json


def object_representation(obj):
    """Returns a representation of the object supplied as an argument"""
    if isinstance(obj, datetime.datetime):
        return obj.replace(tzinfo=datetime.timezone.utc, microsecond=0).isoformat()
    else:
        return obj.__dict__


def json_representation(obj) -> str:
    """Returns the JSON representation of an object"""
    return json.dumps(obj, ensure_ascii=False, indent=4, default=object_representation)
