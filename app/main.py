from fastapi import FastAPI

app = FastAPI(title="Team API")


@app.get("/")
def root():
    return {"message": "Team API is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
