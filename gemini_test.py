from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

print("STARTING")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0
)

print("CLIENT CREATED")

response = llm.invoke(
    "Generate 2 behavioural interview questions for a Python backend engineer."
)

print("\nRESPONSE:\n")
print(response.content)