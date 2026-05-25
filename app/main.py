from fastapi import FastAPI
from openai import OpenAI

app = FastAPI()

client = OpenAI(
    base_url="http://ollama:11434/v1",
    api_key="ollama"
)

@app.get("/")
def hello():
    return {"message": "App is running!"}

@app.post("/ask")
def ask(question: str):
    response = client.chat.completions.create(
        model="qwen2.5:0.5b",
        messages=[{"role": "user", "content": question}]
    )
    return {"answer": response.choices[0].message.content}
