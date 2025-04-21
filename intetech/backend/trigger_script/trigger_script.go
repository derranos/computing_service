package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"sync"
	"time"

	"github.com/jasonlvhit/gocron"
)

type Task struct {
	Name      string
	Priority  int
	Component int
	InputVars []string
}

var taskMap = make(map[string][]Task)
var mutex sync.Mutex

// Структуры
type FunctionTemplate struct {
	Name       string   `json:"name"`
	Body       string   `json:"body"`
	InputVars  []string `json:"inputVars"`
	OutputVars []string `json:"outputVars"`
	Cron       int      `json:"cron"`
}

type Config struct {
	InputVariables    []string           `json:"inputVariables"`
	OutputVariables   []string           `json:"outputVariables"`
	FunctionTemplates []FunctionTemplate `json:"functionTemplates"`
}

// Функция загрузки конфига
func loadConfig(filename string) (Config, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return Config{}, err
	}
	var config Config
	err = json.Unmarshal(data, &config)
	if err != nil {
		return Config{}, err
	}
	return config, nil
}

// topologicalSort выполняет топологическую сортировку и находит компоненты связанности.
func topologicalSort(functions []FunctionTemplate) ([]FunctionTemplate, []int) {
	n := len(functions)
	graph := make(map[int][]int) // Список смежности
	inDegree := make([]int, n)   // Число входящих рёбер
	components := make([]int, n) // Для отслеживания компонент связанности
	sortedFunctions := []FunctionTemplate{}

	// Построение списка смежности и подсчет входящих рёбер
	for i, f1 := range functions {
		for j, f2 := range functions {
			if i != j {
				for _, input := range f2.InputVars {
					for _, output := range f1.OutputVars {
						if input == output {
							graph[i] = append(graph[i], j)
							inDegree[j]++ // Увеличиваем степень входа
							break
						}
					}
				}
			}
		}
	}

	// Поиск стартовых узлов (с inDegree[i] == 0)
	queue := []int{}
	for i := 0; i < n; i++ {
		if inDegree[i] == 0 {
			queue = append(queue, i)
			components[i] = i + 1 // Начинаем номер компоненты с 1
		}
	}
	var realcomponents = make([]int, n)
	var indexes = make([]int, n)
	// Топологическая сортировка (алгоритм Кана)
	index := 0
	for len(queue) > 0 {
		node := queue[0]
		queue = queue[1:]

		sortedFunctions = append(sortedFunctions, functions[node])
		indexes[index] = node
		for _, neighbor := range graph[node] {
			inDegree[neighbor]-- // Уменьшаем число входящих рёбер
			if inDegree[neighbor] == 0 {
				queue = append(queue, neighbor)
			}
			if components[neighbor] != 0 && components[neighbor] != components[node] {
				old := components[neighbor]
				for i, val := range components {
					if val == old {
						components[i] = components[node]
					}
				}
			} else {
				components[neighbor] = components[node]
			}
		}
		index++
	}

	// Проверка на циклы (если не все вершины обработаны)
	if index < n {
		log.Fatal("Циклическая зависимость в графе")
	}
	for i, val := range indexes {
		realcomponents[i] = components[val]
	}
	return sortedFunctions, realcomponents
}

// sendPostRequest отправляет POST-запрос на указанный URL с данными в формате JSON

func sendTask(task Task, timeFunc string) error {
	URL := "http://127.0.0.1:8000/trigger"

	requestData := map[string]interface{}{
		"script":    task.Name,
		"priority":  task.Priority,
		"component": task.Component,
		"inputVars": task.InputVars,
		"wave":      timeFunc,
	}

	jsonData, err := json.Marshal(requestData)
	if err != nil {
		return fmt.Errorf("marshal error: %w", err)
	}

	resp, err := http.Post(URL, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("post error: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		return fmt.Errorf("non-2xx response: %s", resp.Status)
	}

	return nil
}
func sendNewComponent(comp int) {
	URL := "http://127.0.0.1:8000/makeComponent"
	requestData := map[string]interface{}{
		"component": comp,
	}
	jsonData, err := json.Marshal(requestData)
	if err != nil {
		log.Fatal(err)
	}

	// Отправка POST-запроса
	resp, err := http.Post(URL, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		log.Fatal(err)
	}
	defer resp.Body.Close()

	// Выводим ответ от сервера
	//fmt.Println("Response Status:", resp.Status)
}
func processOldestWaveIfNeeded() {
	mutex.Lock()
	defer mutex.Unlock()

	if len(taskMap) <= 2 {
		return
	}

	var oldest string
	first := true

	for k := range taskMap {
		if first || k < oldest {
			oldest = k
			first = false
		}
	}

	tasks := taskMap[oldest]
	delete(taskMap, oldest)

	// Сортировка по приоритету
	sort.Slice(tasks, func(i, j int) bool {
		return tasks[i].Priority < tasks[j].Priority
	})

	// Обработка по 50 штук
	for i := 0; i < len(tasks); i += 50 {
		end := i + 50
		if end > len(tasks) {
			end = len(tasks)
		}
		chunk := tasks[i:end]
		processChunk(chunk, oldest)
	}
}
func processChunk(chunk []Task, timeFunc string) {
	var wg sync.WaitGroup

	for _, task := range chunk {
		wg.Add(1)
		go func(t Task) {
			defer wg.Done()
			err := sendTask(t, timeFunc)
			if err != nil {
				log.Printf("Ошибка при отправке задачи %s: %v\n", t.Name, err)
			}
		}(task)
	}

	wg.Wait() // Ждём, пока все горутины закончат работу
}
func addTaskToMap(task Task, wave string) {
	mutex.Lock()
	taskMap[wave] = append(taskMap[wave], task)
	mutex.Unlock()

	processOldestWaveIfNeeded()
}

func main() {
	filename := filepath.Join("..", "..", "web", "web_page", "static", "config.json")
	config, err := loadConfig(filename)
	if err != nil {
		log.Fatal(err)
	}
	var components []int // Объявляем переменную для компонентов
	config.FunctionTemplates, components = topologicalSort(config.FunctionTemplates)
	var uniqueComponents = make(map[int]bool)
	for _, component := range components {
		uniqueComponents[component] = true
	}
	for key := range uniqueComponents {
		sendNewComponent(key)
	}
	s := gocron.NewScheduler()
	for i, functionTemplate := range config.FunctionTemplates {
		s.Every(uint64(functionTemplate.Cron)).Second().Do(func(script string, priority int, component int, inputVars []string) {
			//fmt.Printf("Function %s is working, cron = %d, priority = %d, component = %d\n", script, functionTemplate.Cron, priority, component)
			addTaskToMap(Task{
				Name:      script,
				Priority:  priority,
				Component: component,
				InputVars: inputVars,
			}, time.Now().UTC().Truncate(time.Second).Format(time.RFC3339))
		}, functionTemplate.Name, i, components[i], functionTemplate.InputVars)
	}

	s.Start()
	fmt.Println("Cron job dispatcher started")

	select {} // Блокировка основного потока
}
