from sanic import Sanic
from sanic.response import text, json
import aiosqlite
import jwt

app = Sanic("HCSA-BACKEND")


@app.listener("before_server_start")
async def setup(app_, loop):
    app_.ctx.db = await aiosqlite.connect("database.db")
    await try_create_db(app_.ctx.db)
    app_.ctx.sessions = {}
    app_.ctx.announcement = ""


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


@app.get("/add_account")
async def add_account(request):
    return text("Account creation is disabled")
    # username = request.args.get("username", None)
    # password = request.args.get("password", None)
    # if username and password:
    #     # add it into the sqlite database
    #     cursor = await request.app.ctx.db.cursor()
    #     await cursor.execute(
    #         "INSERT INTO  accounts VALUES (?, ?, ?)", (username, password, "test")
    #     )
    #     await request.app.ctx.db.commit()
    #     await cursor.close()
    #     return text("Added user to database")


@app.get("/login")
async def login(request):
    username = request.args.get("username", None)
    password = request.args.get("password", None)
    if username and password:
        # check if the user exists in the database
        cursor = await request.app.ctx.db.cursor()
        await cursor.execute(
            "SELECT * FROM accounts WHERE username=? AND password=?", (username, password)
        )
        user = await cursor.fetchone()
        await cursor.close()
        if user:
            # check if the user has an active session
            if username in request.app.ctx.sessions:
                # delete the old session
                del request.app.ctx.sessions[username]

            token = jwt.encode({"username": username}, "secret", algorithm="HS256")
            request.app.ctx.sessions[username] = token
            return text(token)
        return text("Invalid username or password")
    return text("Invalid username or password")


@app.get("/logout")
async def logout(request):
    token = request.args.get("token", None)
    if token:
        for username, session_token in request.app.ctx.sessions.items():
            if session_token == token:
                del request.app.ctx.sessions[username]
                return text("Logged out")
        return text("Invalid token")
    return text("Invalid token")


@app.get("/user")
async def get_user(request):
    token = request.args.get("token", None)
    if token:
        for username, session_token in request.app.ctx.sessions.items():
            if session_token == token:
                cursor = await request.app.ctx.db.cursor()
                await cursor.execute(
                    "SELECT * FROM accounts WHERE username=?", (username,)
                )
                user = await cursor.fetchone()
                await cursor.close()
                return json({"username": user[0], "name": user[2]})
        return text("Invalid token")
    return text("Invalid token")


@app.get("/announcement")
async def announcement(request):
    return text(request.app.ctx.announcement)


@app.get("/set_announcement")
async def set_announcement(request):
    token = request.args.get("token", None)
    if token:
        for username, session_token in request.app.ctx.sessions.items():
            if session_token == token:
                request.app.ctx.announcement = request.args.get("announcement", "")
                return text("Announcement set")
        return text("Invalid token")
    return text("Invalid token")


app.register_listener(setup, "before_server_start")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9200)
