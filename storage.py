# In-memory storage
bots = {}
documents = {}
appointments = {}

# OpenAI API key storage
openai_api_key = None

def set_openai_api_key(key):
    global openai_api_key
    openai_api_key = key