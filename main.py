from sanic import Sanic
from sanic.response import text
import aiosqlite

app = Sanic("HCSA-BACKEND")


@app.listener("before_server_start")
async def setup(app_, loop):
    app_.ctx.db = await aiosqlite.connect("database.db")
    await try_create_db(app_.ctx.db)
    app_.ctx.sessions = {}


async def try_create_db(db):
    cursor = await db.cursor()
    # create the table in the sqlite database
    await cursor.execute(
        "CREATE TABLE IF NOT EXISTS accounts (username TEXT, password TEXT, name TEXT)"
    )
    await db.commit()
    print("Created table users")
    await cursor.close()


@app.middleware("response")
async def cors(request, resp):
    resp.headers.update({"Access-Control-Allow-Origin": "*"})


@app.get("/")
async def hello_world(request):
    username = request.args.get("username", None)
    password = request.args.get("password", None)
    if username and password:
        # add it into the sqlite database
        cursor = await request.app.ctx.db.cursor()
        await cursor.execute(
            "INSERT INTO  accounts VALUES (?, ?, ?)", (username, password, "test")
        )
        await request.app.ctx.db.commit()
        await cursor.close()
        return text("Added user to database")
        return text(f"Hello {username} with password {password}")



app.register_listener(setup, "before_server_start")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9200)
