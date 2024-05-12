import os
from supabase import create_client, Client
from groq import Groq

class SingleGroq:
    _instance_=None
    def __init__(self):
        groqClient = Groq(
                api_key=os.environ.get("GROQ_API_KEY"),
                )
        SingleGroq._instance_ = groqClient
    @classmethod
    def getInstance(cls):
        if cls._instance_:
            return cls._instance_
        else:
            cls()
            return cls._instance_

