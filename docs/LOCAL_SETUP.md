# Local setup and LAN use

## First setup on a new Windows PC

From a PowerShell window inside the cloned repository:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\init.ps1 -InstallSystemDependencies
```

This checks or installs Python 3.12 and FFmpeg with `winget`, creates `backend/.venv`, installs backend dependencies and tools, and runs `npm install` in `frontend`.

Then start the local application:

```powershell
.\scripts\start-dev.ps1 -ProjectRoot .\projects\evaluacion_drone_01 -StopExisting
```

Open `http://127.0.0.1:5173` on that same PC.

## Use from another PC on the same private network

Run the backend and Vite server on the PC that owns the media and should perform the analysis. Find its LAN IPv4 address with `ipconfig`, for example `192.168.1.50`.

On the server PC:

```powershell
.\scripts\start-dev.ps1 `
  -ProjectRoot .\projects\evaluacion_drone_01 `
  -ApiHost 0.0.0.0 `
  -FrontendHost 0.0.0.0 `
  -ApiBaseUrl http://192.168.1.50:8765 `
  -AllowedOrigin http://192.168.1.50:5173 `
  -StopExisting
```

Then open this URL from the editing PC:

```text
http://192.168.1.50:5173
```

The server PC performs FFmpeg/OpenCV analysis and stores SQLite/project artifacts. The second PC is only a browser client. The video files must be readable by the server PC; they do not need to be copied over Wi-Fi.

Allow ports `5173` and `8765` only on the Windows Private network profile if Windows Firewall asks. Do not expose these ports to the public Internet: the current development mode has no authentication.

## GitHub repository setup

The repository must be created under `EditorAgent`, not under the Windows user directory. Verify the local root:

```powershell
git rev-parse --show-toplevel
```

It should end in `Documents/DEV/EditorAgent`.

Create a new empty repository on GitHub, for example `EditorAgent`, without adding a README or license. Then connect and publish:

```powershell
git remote add origin https://github.com/<your-account>/EditorAgent.git
git add .
git commit -m "Initial EditorAgent workspace"
git push -u origin main
```

The `.gitignore` intentionally excludes `backend/.venv`, `frontend/node_modules`, local projects, SQLite databases, analysis artifacts, exports, proxies, and local project registry files. Those must stay on the server PC and should not be uploaded.
