from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from shortener_app.security.exceptions import JsonHTTPException

from .link.short_link.service import get_snowflake_id
from shortener_app.security.auth.transport.router import auth_router
from .link.short_link.transport.router import link_route
from .user.transport.router import me_router
from .database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    print("Создание базы данных")
    yield
    print("Запуск сервера")


app = FastAPI(lifespan=lifespan)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


@app.exception_handler(JsonHTTPException)
async def http_exception_handler_jwt(request, exc: JsonHTTPException):
    return PlainTextResponse(str(exc.content), status_code=status.HTTP_401_UNAUTHORIZED)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    err: list = exc.errors()
    if err: err: dict = err[0]
    err = {"msg" : err.get("msg", "Unexpected Error"), "input": err.get("input")}

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": err, "body": exc.body}),
    )

app.include_router(link_route)
app.include_router(auth_router)
app.include_router(me_router)


origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
