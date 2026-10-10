const path = require("path");
const fs = require("fs");

// Detect unified virtual environment python interpreter if available
const venvPythonLinux = path.resolve(__dirname, ".venv", "bin", "python3");
const venvPythonWin = path.resolve(__dirname, ".venv", "Scripts", "python.exe");

let pythonInterpreter = "python3";
if (fs.existsSync(venvPythonLinux)) {
  pythonInterpreter = venvPythonLinux;
} else if (fs.existsSync(venvPythonWin)) {
  pythonInterpreter = venvPythonWin;
}

const pbExecutable = process.platform === "win32" ? "pocketbase.exe" : "./pocketbase";

module.exports = {
  apps: [
    {
      name: "dramix-pocketbase",
      cwd: "./pocketbase",
      script: pbExecutable,
      args: "serve --http=0.0.0.0:8090",
      autorestart: true,
      watch: false
    },
    {
      name: "dramix-cineflow",
      cwd: "./services/cineflow_hub_api",
      script: "main.py",
      interpreter: pythonInterpreter,
      env: { PORT: 7401, HOST: "127.0.0.1" },
      autorestart: true,
      watch: false
    },
    {
      name: "dramix-wetv",
      cwd: "./services/wetv_api",
      script: "main.py",
      interpreter: pythonInterpreter,
      env: { PORT: 7402, HOST: "127.0.0.1" },
      autorestart: true,
      watch: false
    },
    {
      name: "dramix-kisskh",
      cwd: "./services/kisskh_api",
      script: "server.js",
      env: { PORT: 7403, HOST: "127.0.0.1" },
      autorestart: true,
      watch: false
    },
    {
      name: "dramix-moviebox",
      cwd: "./services/moviebox_api",
      script: "app.py",
      interpreter: pythonInterpreter,
      env: { PORT: 7404, HOST: "127.0.0.1" },
      autorestart: true,
      watch: false
    },
    {
      name: "dramix-viu",
      cwd: "./services/viu_api",
      script: "main.py",
      interpreter: pythonInterpreter,
      env: { PORT: 7405, HOST: "127.0.0.1" },
      autorestart: true,
      watch: false
    },
    {
      name: "dramix-freereels",
      cwd: "./services/freereels_api/production",
      script: "run_proxy.py",
      interpreter: pythonInterpreter,
      env: { PORT: 7406, HOST: "127.0.0.1" },
      autorestart: true,
      watch: false
    },
    {
      name: "dramix-iqiyi",
      cwd: "./services/iqiyi_api/production",
      script: "run_server.py",
      interpreter: pythonInterpreter,
      env: { PORT: 7407, SERVER_PORT: 7407, HOST: "127.0.0.1", SERVER_HOST: "127.0.0.1" },
      autorestart: true,
      watch: false
    }
  ]
};
