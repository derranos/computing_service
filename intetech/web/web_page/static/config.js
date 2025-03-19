const config = {
    apiUrl: "http://127.0.0.1:8000/save",

    // Храним текущие значения переменных
    vars: {
        var1: 0,
        var2: 0,
        var3: 0,
        var4: 0,
        var5: 0
    },

    // Получаем ввод пользователя и проверяем, изменились ли значения
    getUserInput: function() {
        const newVar1 = parseFloat(document.getElementById("var1").value) || 0;
        const newVar2 = parseFloat(document.getElementById("var2").value) || 0;

        // Проверяем, изменились ли данные
        if (newVar1 !== this.vars.var1 || newVar2 !== this.vars.var2) {
            this.vars.var1 = newVar1;
            this.vars.var2 = newVar2;
            return true; // Если данные изменились
        } else {
            return false; // Если данные не изменились
        }
    },

    calc_var3: function() {
        this.vars.var3 = this.vars.var1 + this.vars.var2;
        return this.vars.var3;
    },

    calc_var4: function() {
        this.vars.var4 = this.vars.var3 * this.vars.var3;
        return this.vars.var4;
    },

    calc_var5: function() {
        this.vars.var5 = this.vars.var3 * 2;
        return this.vars.var5;
    }
};
