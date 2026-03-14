from fastapi import FastAPI

from app.routes import auth, invitations, organizations, users

app = FastAPI(title="Team API")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(organizations.router, prefix="/api/v1")
app.include_router(invitations.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "Team API is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
