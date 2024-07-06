# test_langchain.py
try:
    from langchain.document_loaders import TextLoader
    from langchain.indexes import VectorstoreIndexCreator
    from langchain.llms import OpenAI

    print("langchain modules imported successfully.")
except ImportError as e:
    print(f"ImportError: {e}")
