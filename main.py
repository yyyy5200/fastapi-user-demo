from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pymysql
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 解决跨域问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库连接配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",  # 改成你的MySQL密码
    "database": "test_db",
    "charset": "utf8mb4"
}

# ========== 请求体模型 ==========
class UserCreate(BaseModel):
    name: str
    age: int

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None

# ========== 工具函数：获取数据库连接 ==========
def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

# ========== 接口 ==========
@app.get("/")
def read_root():
    return {"message": "用户管理系统 API"}

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong!"}

# 1. 查询所有用户
@app.get("/users")
def get_users():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, age FROM users ORDER BY id")
            result = cursor.fetchall()
            # 转成字典列表
            users = [{"id": row[0], "name": row[1], "age": row[2]} for row in result]
            return users
    finally:
        conn.close()

# 2. 新增用户
@app.post("/users")
def create_user(user: UserCreate):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 参数化查询，防SQL注入
            sql = "INSERT INTO users (name, age) VALUES (%s, %s)"
            cursor.execute(sql, (user.name, user.age))
            conn.commit()
            return {"id": cursor.lastrowid, "name": user.name, "age": user.age}
    finally:
        conn.close()

# 3. 修改用户（PUT）
@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 先查一下用户是否存在
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="用户不存在")
            
            # 动态拼接 SET 语句
            updates = []
            values = []
            if user.name is not None:
                updates.append("name = %s")
                values.append(user.name)
            if user.age is not None:
                updates.append("age = %s")
                values.append(user.age)
            
            if not updates:
                raise HTTPException(status_code=400, detail="没有要更新的字段")
            
            values.append(user_id)
            sql = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(sql, values)
            conn.commit()
            return {"message": "更新成功", "id": user_id}
    finally:
        conn.close()

# 4. 删除用户
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 先查是否存在
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="用户不存在")
            
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            return {"message": "删除成功", "id": user_id}
    finally:
        conn.close()