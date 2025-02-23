import uuid
from typing import Union, NewType

UUID_STR = Union[uuid.UUID, str]

URL_ID = NewType("URL_ID", int)

def get_random_uuid_as_str():
    return str(uuid.uuid4())
