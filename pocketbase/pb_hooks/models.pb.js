routerAdd("GET", "/api/modelles/models", (e) => {
    const records = $app.findAllRecords("providers");

    const items = records.map(item => {
        return "{" +
            '"id":' + JSON.stringify(item.get("provider_id")) + "," +
            '"name":' + JSON.stringify(item.get("name")) + "," +
            '"icon_url":' + JSON.stringify(item.get("icon_url")) + "," +
            '"description":' + JSON.stringify(item.get("description")) + "," +
            '"content_type":' + JSON.stringify(item.get("content_type")) + "," +
            '"status":' + JSON.stringify(item.get("status")) +
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