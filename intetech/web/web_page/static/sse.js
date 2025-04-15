const fs = require('fs');
const readline = require('readline');

// Очередь для обработки запросов
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

// Загружаем конфигурацию один раз
let config = null;
try {
  const rawData = fs.readFileSync('config.json', 'utf8');
  config = JSON.parse(rawData);
} catch (err) {
  console.error('Ошибка при загрузке config.json:', err.message);
  process.exit(1);
}

// Поиск функции по имени
function findFunctionByName(functionName) {
  return config.functionTemplates.find(func => func.name === functionName);
}

// Асинхронная обработка задачи
function processTask(task_name, values) {
  const template = findFunctionByName(task_name);

  if (!template) {
    process.stdout.write(`error Function ${task_name} not found\n`);
    return;
  }

  const params = template.inputVars.map((_, i) => `x${i + 1}`);
  const func = new Function(...params, template.body);

  try {
    const result = func(...values); // Выполняем задачу (можно делать асинхронным)
    const outputName = template.outputVars[0] || 'result';
    process.stdout.write(`${outputName} ${result}\n`);
  } catch (err) {
    process.stdout.write(`error ${err.message}\n`);
  }
}

// Обработка входящих сообщений
rl.on('line', async (line) => {
  const { task_name, values } = JSON.parse(line);

  // Параллельная обработка: запускаем задачу асинхронно
  processTask(task_name, values); // Каждое обращение выполняется в своей корутине
});
