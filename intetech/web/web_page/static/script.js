window.onload = () => {
    const inputContainer = document.getElementById('inputFields');
    const outputContainer = document.getElementById('outputFields');

    // Создаём поля ввода
    window.config['inputVariables'].forEach(variable => {
        inputContainer.innerHTML += `
            <label>${variable}: </label>
            <input type="text" id="${variable}"><br>
        `;
    });

    // Создаём поля вывода (только для чтения)
    window.config['outputVariables'].forEach(variable => {
        outputContainer.innerHTML += `
            <label>${variable}: </label>
            <input type="text" id="${variable}" readonly value="[пусто]"><br>
        `;
    });
};
