import uuid
from typing import Union

UUID_STR = Union[uuid.UUID, str]


def get_random_uuid_as_str():
    return str(uuid.uuid4())
