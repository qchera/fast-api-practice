from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.exceptions import add_exception_handlers
from .core.redis import init_redis, close_redis
from .routers.master_router import master_router
from .database.session import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    await init_redis()

    yield

    await close_redis()

app = FastAPI(lifespan = lifespan)

add_exception_handlers(app)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(master_router)