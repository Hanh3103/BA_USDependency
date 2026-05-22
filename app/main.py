from fastapi import FastAPI
from openai import OpenAI

app = FastAPI()

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

@app.get("/")
def hello():
    return {"message": "App is running!"}

@app.post("/ask")
def ask(question: str):
    response = client.chat.completions.create(
        model="gemma:latest",
        messages=[{"role": "user", "content": question}]
    )
    return {"answer": response.choices[0].message.content}