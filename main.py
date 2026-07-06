from fastapi import FastAPI
import pymysql

app = FastAPI()

# 数据库连接配置
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="123456",  # ⚠️ 改成你安装 MySQL 时设置的密码
        database="test_db",
        cursorclass=pymysql.cursors.DictCursor
    )

@app.get("/")
def read_root():
    return {"message": "Hello World! 我的接口已经连上数据库了！"}

@app.get("/users")
def get_users():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        result = cursor.fetchall()
    conn.close()
    return {"data": result, "count": len(result)}

from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    age: int

@app.post("/users")
def create_user(user: UserCreate):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (name, age) VALUES (%s, %s)",
            (user.name, user.age)
        )
        conn.commit()
        new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "name": user.name, "age": user.age, "message": "创建成功"}