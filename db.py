import os
from supabase import create_client, Client

class SingleDb:
    _instance_=None
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        supabase: Client = create_client(url, key)
        SingleDb._instance_ = supabase
    @classmethod
    def getInstance(cls):
        if cls._instance_:
            return cls._instance_
        else:
            cls()
            return cls._instance_