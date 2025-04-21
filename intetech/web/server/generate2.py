import json

def generate_variables(num_variables):
    variables = {}

    # Начальные переменные
    initial_values = [1, -1, 0, 0, 0]

    for i in range(1, num_variables + 1):
        # Присваиваем значение по циклу из initial_values
        value = initial_values[(i - 1) % len(initial_values)]
        variables[f"x{i}"] = value

    return variables

# Генерация 200 переменных
num_variables = 400
variables = generate_variables(num_variables)

# Сохранение в файл
with open('start_config.json', 'w') as f:
    json.dump(variables, f, indent=4)

print(f"Generated {num_variables} variables and saved to 'variables.json'")
