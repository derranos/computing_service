async function updateData1() {
    let userInput = config.getUserInput(); 

    // Проверяем, изменились ли var1 или var2
    if (userInput) {
        let var3 = config.calc_var3();
        let var4 = config.calc_var4();

        // Обновляем только если изменились значения
        document.getElementById("var3").value = var3;
        document.getElementById("var4").value = var4;
    }

    // Отправляем актуальные данные на сервер
    let response = await fetch(config.apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config.vars)  // Отправляем текущее состояние
    });

    let data = await response.json();
    console.log(data);
}

async function updateData2() {
    let var5 = config.calc_var5();

    // Обновляем значения
    document.getElementById("var5").value = var5;

    // Отправляем актуальные данные на сервер
    let response = await fetch(config.apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config.vars)  // Отправляем текущее состояние
    });

    let data = await response.json();
    console.log(data);
}
