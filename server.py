from os import environ

if not environ.get("PROD"):
    from dotenv import load_dotenv

    load_dotenv()

import asyncpg
from sanic import Request, Sanic, json
from sanic.exceptions import ServiceUnavailable, Unauthorized
from sanic.log import logger

app = Sanic(__name__)
ServiceUnavailable.quiet = False
QUERY = "SELECT 1"


@app.before_server_start
async def setup_pool(app: Sanic):
    app.ctx.asyncpg = await asyncpg.create_pool(
        dsn=app.config.DSN,
        min_size=app.config.MIN_SIZE,
        max_size=app.config.MAX_SIZE,
        max_inactive_connection_lifetime=app.config.MAX_INACTIVE_CONNECTION_LIFETIME,
        max_queries=app.config.MAX_QUERIES,
        statement_cache_size=0,
    )


@app.after_server_stop
async def close_pool(app: Sanic):
    await app.ctx.asyncpg.close()


@app.on_request
async def auth(request: Request):
    if request.token != request.app.config.TOKEN:
        raise Unauthorized("Auth required.", scheme="Bearer")


@app.get("/nopool")
async def asyncpg_dummy_nopool(request):
    conn = await asyncpg.connect(request.app.config.DSN)
    result = await conn.fetchval(QUERY)
    return json({"result": result})


@app.get("/pool")
async def asyncpg_dummy_pool(request):
    async with request.app.ctx.asyncpg.acquire() as conn:
        result = await conn.fetchval(QUERY)
    return json({"result": result})


@app.get("/clear")
async def clear(request):
    logger.warning("clear")
    return json(None)
