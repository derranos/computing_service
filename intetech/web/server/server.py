from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from influxdb_client import InfluxDBClient
from datetime import datetime, timezone
from influxdb_client.client.write_api import SYNCHRONOUS
import heapq


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
task_queues = {}  # Очереди задач по компонентам
workers = {}  # Запущенные обработчики задач
# Модель для входных данных
class InputData(BaseModel):
    var1: float
    var2: float
    var3: float
    var4: float
    var5: float

class TaskRequest(BaseModel):
    script: str
    priority: int
    component: int
    inputVars: list
    wave: str

class Component(BaseModel):
    component: int
# Раздача папки static (JS, CSS и другие файлы)
app.mount("/static", StaticFiles(directory=web_page_path / "static"), name="static")


# Путь к файлу конфигурации JSON
config_file_path = Path(__file__).parent.parent / "web_page"  / "static" / "start_config.json"
# Подключение к базе
token = "db0Kwn-9n-ovlDsUBBTLn3GkucFvlkg5QOVNegaX9jaS2DKzpnsOCb4ddDK2IeLuEdbWv5n34rENti0iNEtNUQ=="
org = "myorg"
bucket = "mybucket"
url = "http://localhost:8086"
client = InfluxDBClient(url=url, token=token, org=org)

# Чтение данных из JSON-файла
def load_data_from_json():
    try:
        with open(config_file_path, "r") as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="JSON file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Error parsing JSON file")

async def write_to_db(data, client: InfluxDBClient, bucket, org, wave, tag = 'start'):
    with client.write_api(write_options=SYNCHRONOUS) as write_api:
        for measurement, value in data.items():
            point = {
                "measurement": 'vars',
                "tag" : {"var": tag},
                "fields": {f"{measurement}": value},
                "time": wave
            }
            # print(point)
            write_api.write(bucket=bucket, record=point, org=org)
    return True

async def get_from_db(vars, client: InfluxDBClient, bucket, org):
    query_api = client.query_api()

    field_filter = " or ".join([f'r["_field"] == "{v}"' for v in vars])
    
    query = f'''
        from(bucket: "{bucket}")
        |> range(start: -1h)
        |> filter(fn: (r) => r["_measurement"] == "vars")
        |> filter(fn: (r) => {field_filter})
        |> last()
    '''

    result = query_api.query(org=org, query=query)

    values = [record.get_value() for table in result for record in table.records]
    return values
    
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
        print(f"Отправка события: {data}")
        yield f"data: {data}\n\n"

# Эндпоинт для SSE (отправка данных клиентам)
@app.get("/sse")
async def sse():
    queue = asyncio.Queue()
    clients.append(queue)  # Добавляем клиента в список
    return StreamingResponse(event_generator(queue), media_type="text/event-stream")

# Обработчик задач
@app.post("/trigger")
async def trigger(task: TaskRequest):
    comp = task.component
    if comp not in task_queues:
        task_queues[comp] = []  # Создаём очередь для компоненты
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    heapq.heappush(task_queues[comp], (task.priority, task.script, task.inputVars, task.wave, future))
    # Запускаем обработчик для компоненты, если его нет
    if comp not in workers:
        workers[comp] = asyncio.create_task(process_component_tasks(comp))
    await future  # Ждем завершения задачи
    return {"status": "ok"}

# Обработчик задач для компоненты
async def process_component_tasks(comp):
    #print('Запущен обработчик для компоненты:', comp)
    await asyncio.sleep(0.05)
    while task_queues[comp]:
        # Извлекаем с наивысшим приоритетом
        _, task_name, inputVars, wave, future = heapq.heappop(task_queues[comp])
        vals = await get_from_db(inputVars, client, bucket, org)
        
        # print('Получены значения:', vals, task_name)
        res = await execute_task(task_name, vals, comp)
        # print('Ответ', res)
        if res:
            await write_to_db({res[0]: int(res[1])}, client, bucket, org, wave, 'update')
            # print('Записано в БД:', {res[0]: int(res[1])})
            future.set_result("done") 
        else:
            future.set_exception("error")
    del workers[comp]  # Удаляем обработчик, когда все задачи выполнены
# Выполнение задачи
async def execute_task(task_name, vals, comp):
    if not node_proc[comp]:
        raise RuntimeError("Node.js worker is not running")

    payload = json.dumps({"task_name": task_name, "values": vals}) + '\n'
    
    try:
        node_proc[comp].stdin.write(payload.encode())
        await node_proc[comp].stdin.drain()

        line = await node_proc[comp].stdout.readline()
        response = line.decode().strip().split()

        if response[0] == "error":
            raise RuntimeError("Node worker error: " + " ".join(response[1:]))

        return response
    except Exception as e:
        raise RuntimeError(f"Failed to execute task: {str(e)}")

node_proc = {}
@app.post("/makeComponent")
async def startup_event(Com: Component):
    node_proc[Com.component] = await asyncio.create_subprocess_exec(
        'node',
        str(web_page_path / 'static' / 'sse.js'),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Дополнительный лог для ошибок Node.js
    #asyncio.create_task(log_worker_errors(node_proc[Com.component].stderr))


async def log_worker_errors(stderr):
    while True:
        line = await stderr.readline()
        if not line:
            break
        print(f"[Node.js ERROR] {line.decode().strip()}")

if __name__ == "__main__":
    delete_api = client.delete_api()

    # Формируем запрос для удаления всех данных
    delete_api.delete(
        '1970-01-01T00:00:00Z',  # Начало периода (дата, с которой начинается удаление)
        '2040-01-01T00:00:00Z',  # Конец периода (например, можно взять будущее, чтобы всё удалить)
        bucket=bucket,
        org=org,
        predicate='_measurement="vars"' # Условие удаления (в данном случае удаляем все данные)
    )
    asyncio.run(write_to_db(load_data_from_json(), client, bucket, org, datetime.now(timezone.utc).isoformat()))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)