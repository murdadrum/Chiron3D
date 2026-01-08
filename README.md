# 🏹 Chiron — Interactive AI Sidecar for Blender

[![Status](https://img.shields.io/badge/Status-Phase_1:_Simulation-blueviolet?style=for-the-badge)](https://github.com/murdadrum/Chiron)
[![Stack](https://img.shields.io/badge/Tech-React_•_Vite_•_Node_•_Python_•_Vertex_AI-blue?style=for-the-badge)]()
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)]()

Chiron is a guided, AI-driven tutorial platform that runs inside Blender. The web-based "Sidecar" UI (React/Vite) acts as the lesson engine while a lightweight Blender addon (Python) executes safe, deterministic demo steps and highlights UI elements.

---

## ✨ Features & Highlights

- **Context-Aware Lessons**: Generate short, interactive steps using Vertex AI (Gemini).
- **Sidecar UI**: A React-based interface that visualizes lesson progression and maps.
- **Safe Command Bridge**: Forwards structured lesson JSON to Blender to execute whitelisted commands (ADD_CUBE, SELECT_OBJECT, etc.).
- **TTS Integration**: Built-in Text-to-Speech support for step instructions.
- **Safety First**: No arbitrary Python execution; all incoming commands are validated against a whitelist.

---

## 🚀 Quick Start (macOS)

The repository includes a launcher that handles GCP authentication and starts both backend and frontend services in separate terminal tabs.

```bash
# 1. Make scripts executable
chmod +x launch_chiron.command tools/install_and_run.sh

# 2. Run the one-click launcher
./launch_chiron.command
```

Wait for the terminal tabs to open and the services to start.
- **Backend**: http://localhost:5001
- **Frontend**: http://localhost:5173 (or as shown in Vite logs)

---

## 🛠 Manual Setup (Developer Flow)

### 1. Backend Server
```bash
cd server
npm install
# Use USE_MOCK_MCP=true for local testing without a live MCP server
USE_MOCK_MCP=true node index.js
```

### 2. Sidecar UI
```bash
cd web
npm install
npm run dev
```

### 3. Blender Add-on
Open Blender → **Preferences** → **Add-ons** → **Install** → Select `chiron/gemini_addon.py` and enable it.
> [!NOTE]
> For a more integrated experience, vendor `blender-mcp` under `third_party/` to use the full MCP bridge functionality.

---

## 🎬 Demo Script

1. **Open UI**: Navigate to the Sidecar UI in your browser.
2. **Setup Chat**: Toggle "Detailed steps" in the header if you want granular instructions.
3. **Ask Chiron**: Request a tutorial, e.g., *"Create a simple cube and color it"*.
4. **Playback**: Walk through the generated steps. Observe the lesson JSON being forwarded.
5. **Verify**: Check the mock logs (or Blender console) to see the `SPEAK` and `ADD_CUBE` commands being received.

---

## 📐 Architecture

- **Brain (Guide)**: React + Vite — Handles the lesson map, UI, and user prompts.
- **Backend**: Node.js + Express — Orchestrates Gemini AI calls and serves the API.
- **Bridge**: HTTP Proxy — Forwards lesson JSON to the Blender MCP server.
- **Hands**: Blender Addon (Python) — Executes whitelisted commands using `bpy`.

---

## 📁 Project Layout

```
Chiron/
├─ chiron/               # Blender addon loader + listener
├─ server/               # Node.js backend (AI orchestration)
├─ web/                  # Primary React/Vite Sidecar UI
├─ demo/                 # Alternative/Legacy frontend demo
├─ data/                 # Manual extraction & conversion scripts
├─ docs/                 # Integration & developer docs
├─ tools/                # Launch scripts & schemas
└─ third_party/          # Submodules and external dependencies
```

---

## 🛡 Safety & Security

- **Whitelisted Commands**: Incoming lesson `command` tokens are mapped to specific, safe Python handlers.
- **Local-Only**: The internal bridge defaults to `localhost`. Use `MCP_AUTH_TOKEN` for any non-local deployments.

---

Maintainers: **murdadrum** & contributors  
License: **MIT**
