routerAdd("GET", "/api/modelles/models", (e) => {
    const records = $app.findAllRecords("providers");

    const priority = {
        "wetv": 1,
        "moviebox": 2,
        "viu": 3,
        "kisskh": 4,
        "iqiyi": 5,
        "youku": 6,
        "freereels": 7
    };

    const rawList = records.map(item => {
        return {
            id: item.get("provider_id"),
            name: item.get("name"),
            icon_url: item.get("icon_url"),
            description: item.get("description"),
            content_type: item.get("content_type"),
            status: item.get("status")
        };
    });

    rawList.sort((a, b) => {
        const idA = (a.id || "").toLowerCase();
        const idB = (b.id || "").toLowerCase();
        const rankA = priority[idA] !== undefined ? priority[idA] : 999;
        const rankB = priority[idB] !== undefined ? priority[idB] : 999;
        if (rankA !== rankB) {
            return rankA - rankB;
        }
        const nameA = (a.name || "").toLowerCase();
        const nameB = (b.name || "").toLowerCase();
        return nameA < nameB ? -1 : (nameA > nameB ? 1 : 0);
    });

    const items = rawList.map(item => {
        return "{" +
            '"id":' + JSON.stringify(item.id) + "," +
            '"name":' + JSON.stringify(item.name) + "," +
            '"icon_url":' + JSON.stringify(item.icon_url) + "," +
            '"description":' + JSON.stringify(item.description) + "," +
            '"content_type":' + JSON.stringify(item.content_type) + "," +
            '"status":' + JSON.stringify(item.status) +
        "}";
    });

    const jsonStr = "{" +
        '"code":200,' +
        '"message":"success",' +
        '"data":[' + items.join(",") + "]," +
        '"searchall_short_drama":false,' +
        '"searchall_movie":true' +
    "}";

    return e.blob(200, "application/json", jsonStr);
});