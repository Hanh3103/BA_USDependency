from fastapi import FastAPI
from fastapi.responses import JSONResponse

from errors import AppError, LLMConnectionError
from stages.annotation import run as annotation_run
from connectionsHandle.ollama_connection import create_chat_completion

app = FastAPI()


@app.exception_handler(LLMConnectionError)
def llm_connection_error_handler(_, exc: LLMConnectionError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(AppError)
def app_error_handler(_, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )

@app.get("/")
def hello():
    return {"message": "App is running!"}

@app.post("/ask")
def ask(question: str):
    response = create_chat_completion(messages=[{"role": "user", "content": question}])
    return {"answer": response.choices[0].message.content}

@app.post("/annotate")
def annotate(user_story: str):
    annotation = annotation_run(user_story)
    return {"annotation": annotation}
