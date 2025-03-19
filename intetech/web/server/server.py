from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI()

origins = ['http://localhost:8000', 'http://127.0.0.1:8000']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # Разрешенные источники
    allow_credentials=True,       # Разрешить куки и аутентификационные заголовки
    allow_methods=["*"],          # Разрешить все методы
    allow_headers=["*"],          # Разрешить любые заголовки 
)

web_page_path = Path(__file__).parent.parent / "web_page"  # Путь к папке с веб-страницей
data_store = {}  # Хранилище данных (можно заменить на базу данных)
clients = []  # Список клиентов SSE (Server-Sent Events)
task_queue = asyncio.Queue()  # Очередь задач

# Модель для входных данных
class InputData(BaseModel):
    var1: float
    var2: float
    var3: float
    var4: float
    var5: float

# Раздача папки static (JS, CSS и другие файлы)
app.mount("/static", StaticFiles(directory=web_page_path / "static"), name="static")

# Отдаем index.html при заходе на /
@app.get("/")
async def serve_index():
    return FileResponse(web_page_path / "index.html")

# Сохраняем данные
@app.post("/save")
async def save_data(data: InputData):
    data_store["values"] = data.dict()
    return {"message": "Data saved", "data": data_store["values"]}

# Получаем сохраненные данные
@app.get("/get")
async def get_data():
    return data_store.get("values", {})

# Генератор событий для SSE (отправка данных клиентам)
async def event_generator(queue):
    while True:
        data = await queue.get()
        yield f"data: {data}\n\n"

# Эндпоинт для SSE (отправка данных клиентам)
@app.get("/sse")
async def sse():
    queue = asyncio.Queue()
    clients.append(queue)  # Добавляем клиента в список
    return StreamingResponse(event_generator(queue), media_type="text/event-stream")

# Обработчик задач
@app.post("/trigger")
async def trigger(request: Request):
    body = await request.json()
    script_name = body.get("script")

    if script_name:
        await task_queue.put(script_name)  # Добавляем задачу в очередь
    return {"status": "ok"}

# Рабочий процесс для выполнения задач
async def task_worker():
    while True:
        task_list = []
        # Собираем задачи из очереди
        while not task_queue.empty():
            task_list.append(await task_queue.get())

        # Гарантируем выполнение cron-1 перед cron-2
        if "cron-1" in task_list:
            await execute_task("cron-1")
        if "cron-2" in task_list:
            await execute_task("cron-2")
        await asyncio.sleep(0.2)  # Задержка между проверками очереди

# Функция для выполнения задачи
async def execute_task(task_name):
    for queue in clients:
        await queue.put(task_name)  # Отправляем задачу клиентам
    print(f"Выполнено: {task_name}")

# Запускаем обработчик задач при старте приложения
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(task_worker())  # Запускаем асинхронную задачу

# Запуск сервера при запуске скрипта
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)