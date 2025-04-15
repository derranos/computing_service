import json

def generate_function_templates(num_templates):
    function_templates = []

    # Начальные данные
    base_functions = [
        {
            "name": "f0",
            "body": "return x1 * -1",
            "inputVars": ["1"],
            "outputVars": ["1"],
            "cron": 5
        },
        {
            "name": "f1",
            "body": "return x1 * -1;",
            "inputVars": ["2"],
            "outputVars": ["2"],
            "cron": 5
        },
        {
            "name": "f2",
            "body": "return 2 + x1 + x2;",
            "inputVars": ["1", "2"],
            "outputVars": ["3"],
            "cron": 1
        },
        {
            "name": "f3",
            "body": "return x2 + x1;",
            "inputVars": ["3", "1"],
            "outputVars": ["4"],
            "cron": 5
        },
        {
            "name": "f4",
            "body": "return x2 + x1;",
            "inputVars": ["3", "1"],
            "outputVars": ["5"],
            "cron": 1
        }
    ]

    # Генерация всех шаблонов
    offset = 0
    for i in range(num_templates):
        base_function = base_functions[i % len(base_functions)].copy()

        # Обновляем название
        base_function["name"] = f"f{i}"

        # Обновляем входные и выходные переменные
        # Переменные будут увеличиваться на 5 для каждой новой функции
        if i!= 0 and i % 5 == 0:
            offset += 5
        base_function["inputVars"] = [f"x{offset + int(j)}" for j in base_function["inputVars"]]
        base_function["outputVars"] = [f"x{offset + int(j)}" for j in base_function["outputVars"]]

        function_templates.append(base_function)

    return function_templates

# Генерация 200 шаблонов
num_templates = 50
function_templates = generate_function_templates(num_templates)

# Сохранение в файл
with open('config.json', 'w') as f:
    json.dump({"functionTemplates": function_templates}, f, indent=4)

print(f"Generated {num_templates} function templates and saved to 'function_templates.json'")
