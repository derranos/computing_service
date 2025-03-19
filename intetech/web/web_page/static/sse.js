// Подключаемся к SSE
const eventSource = new EventSource("http://127.0.0.1:8000/sse");

// Когда приходит сообщение, вызываем функцию расчета из другого файла
eventSource.onmessage = function(event) {
    console.log("Получено сообщение:", event.data);
    if (event.data == "cron-1") {
        updateData1();
    }
    else if (event.data == "cron-2") {
        updateData2();
    }
};
