from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.applications import Starlette


from starlette_admin import I18nConfig
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.auth import AdminConfig, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed



from shortener_app.security.exceptions import JsonHTTPException

from .link.short_link.service import get_snowflake_id
from shortener_app.security.auth.transport.router import auth_router
from .link.short_link.transport.router import link_route
from .user.transport.router import me_router
from .database import create_tables, async_engine, models


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    print("Создание базы данных")
    yield
    print("Запуск сервера")


app = FastAPI(lifespan=lifespan)
# Instrumentator().instrument(app).expose(app)



class SimpleAuthProvider(AuthProvider):
    async def login(
        self,
        username: str,
        password: str,
        request: Request,
        response: Response,
        remember_me: bool = False,
    ) -> Response:
        if username != "admin" or password != "admin":
            raise LoginFailed("Invalid username or password")
        
        response = RedirectResponse(url="/a/admin", status_code=303)
        response.set_cookie(key="admin-auth", value="simple-token")
        return response


    async def is_authenticated(self, request: Request) -> bool:
        return request.cookies.get("admin-auth") == "simple-token"


    async def get_admin_user(self, request: Request) -> dict:
        if await self.is_authenticated(request):
            return {"username": "admin"}
        return None


    async def logout(self, request: Request, response: Response) -> Response:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="admin-auth")
        return response
    
i18n_config = I18nConfig(
    default_locale="ru",
    language_switcher=["ru", "en"]  # Скрываем переключатель языков, если нужен только русский
)
admin = Admin(
    engine=async_engine, 
    title="ShortLink admin panel", 
    auth_provider=SimpleAuthProvider(),
    i18n_config=i18n_config,
)
admin.add_view(ModelView(models.APIUser))
admin.add_view(ModelView(models.URL))
admin.add_view(ModelView(models.UrlMetric))
admin.add_view(ModelView(models.AuthUserUrl))
admin.add_view(ModelView(models.IssuedJWTToken))

admin_app = Starlette()
admin.mount_to(admin_app)
app.mount("/a", admin_app)


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
