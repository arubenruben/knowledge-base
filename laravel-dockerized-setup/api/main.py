from environs import Env
from api.routers import v1
from fastapi import FastAPI
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.env = Env()
    app.state.env.read_env(override=True)

    yield


app = FastAPI(lifespan=lifespan)

app.include_router(v1.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
