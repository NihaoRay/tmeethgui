import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from license_manager import generate_license
import os


app = FastAPI()

# ⚠️ 极其重要：配置跨域资源共享 (CORS)
# 因为前端页面（比如在浏览器直接打开）和后端（端口8000）属于不同源，必须允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有前端地址访问
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有请求方法 (GET, POST等)
    allow_headers=["*"],
)

# 定义前端传过来的 JSON 数据格式
class CodeRequest(BaseModel):
    user_input: str

# 定义一个 POST 接口接收请求
@app.post("/api/generate_code")
def generate_code(request: CodeRequest):
    # 1. 接收到前端传来的用户输入
    print(f"收到请求，用户输入为: {request.user_input}")

    # 2. 生成激活码 (这里用 UUID 截取前8位作为示例)
    machine_code = request.user_input
    license_key = "没有输入"
    if machine_code:
        license_key = generate_license(machine_code)

    # 3. 将结果返回给前端
    return {
        "code": 200,
        "message": "激活码生成成功",
        "data": {
            "original_input": request.user_input,
            "activation_code": license_key
        }
    }


# 2. 挂载 Vue 的静态资源 (非常重要：这段代码必须放在 API 路由的下面)
# 挂载 assets 文件夹（存放 js 和 css）
app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

# 3. 拦截所有其他请求，返回 Vue 的 index.html
@app.get("/{catchall:path}")
async def serve_vue_app(catchall: str):
    # 检查 dist/index.html 是否存在
    if os.path.exists("dist/index.html"):
        return FileResponse("dist/index.html")
    return {"error": "前端文件未找到，请检查 dist 目录"}

# 运行命令：uvicorn main:app --reload

# 加入下面这段代码
if __name__ == "__main__":
    # 注意：调试的时候，千万不要加 reload=True
    uvicorn.run("tmeetgui-web:app", host="0.0.0.0", port=8000)