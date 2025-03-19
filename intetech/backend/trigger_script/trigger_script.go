package main

import (
	"bytes"
	"fmt"
	"log"
	"net/http"

	"github.com/jasonlvhit/gocron"
)

func sendPostRequest(scriptName string) {
	// URL для POST-запроса
	URL := "http://python-server:8000/trigger"

	// Создаем данные для тела запроса (включаем название скрипта)
	data := []byte(fmt.Sprintf(`{"script": "%s"}`, scriptName))

	// Выполнение POST-запроса с телом запроса
	resp, err := http.Post(URL, "application/json", bytes.NewBuffer(data))
	if err != nil {
		log.Printf("Ошибка при отправке запроса: %v", err)
		return
	}
	defer resp.Body.Close()

	fmt.Println("Команда отправлена для скрипта:", scriptName, "Статус:", resp.Status)
}

func main() {
	s := gocron.NewScheduler()

	// Планируем выполнение задачи каждую 4 секунды
	s.Every(10).Second().Do(func() {
		fmt.Println("Cron job 1 выполняется")
		sendPostRequest("cron-1")
	})

	// Планируем выполнение задачи каждую 5 секунду
	s.Every(15).Second().Do(func() {
		fmt.Println("Cron job 2 выполняется")
		sendPostRequest("cron-2")
	})

	s.Start()

	fmt.Println("Cron job dispatcher started")

	// Блокируем основную горутину, чтобы программа не завершилась сразу
	select {}
}
