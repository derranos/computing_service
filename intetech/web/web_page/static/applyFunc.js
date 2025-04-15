function applyFunctionByName(functionName) {
    // Находим шаблон функции по имени
    const template = window.config['functionTemplates'].find(template => template.name === functionName);
    
    if (!template) {
        console.log(`Функция ${functionName} не найдена.`);
        return;
    }

    // Получаем значения переменных с сайта
    const inputValues = template.inputVars.map(varName => {
        const inputElement = document.getElementById(varName);
        return Number(inputElement.value) || 0;  
    });

    // Создаем массив для параметров функции x1, x2, ..., xN
    const params = template.inputVars.map((varName, index) => `x${index + 1}`);

    // Создаем функцию с параметрами x1, x2, ..., xN
    const func = new Function(...params, template.body);

    // Выполняем функцию с реальными значениями
    const result = func(...inputValues);  

    // Записываем результат в выходные переменные
    template.outputVars.forEach(outputVar => {
        const outputElement = document.getElementById(outputVar);
        outputElement.value = result;  
    });
}
