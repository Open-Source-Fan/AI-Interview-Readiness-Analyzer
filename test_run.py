print("STARTING TEST")

from dotenv import load_dotenv
load_dotenv()

print("ENV LOADED")

from langchain_openai import ChatOpenAI

print("IMPORTS OK")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

print("CLIENT CREATED")

response = llm.invoke("Say hello in one sentence.")

print("API RESPONSE:")
print(response.content)