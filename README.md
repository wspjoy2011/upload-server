# 📷 Image Hosting Server

A lightweight containerized service for uploading, viewing, and managing images via a browser interface.  
It features a drag-and-drop uploader, automatic URL generation, image listing with delete support, and persistent logging — all powered by a clean backend + frontend separation and managed with Docker Compose.

---

## ✨ Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)

---

## 📌 Overview

This project is a mini fullstack service built for uploading and sharing images through a clean UI.  
It includes:

- A **backend server** written in Python (no frameworks, just `http.server`)
- A modern **frontend UI** with drag-and-drop support
- **Nginx reverse proxy** with multi-port load balancing
- **Logging** of all backend and access events
- Simple REST API with routes for uploading, listing, and deleting images

All components are containerized and orchestrated via `docker-compose`.

---

## 🚀 Features

- **📤 Upload via Drag & Drop or Button**  
  Users can upload `.jpg`, `.png`, or `.gif` images by clicking a button or dragging files into the UI.

- **🧾 Image Listing Table**  
  Uploaded images are listed in a styled table with preview icons and full shareable URLs.

- **🗑 Delete Support**  
  Each image row includes a trash icon to delete the file immediately from the server.

- **🔁 Live Tab Switching**  
  The UI allows switching between "Upload" and "Images" views without reloading the page.

- **🧠 Error Feedback**  
  All user errors (bad type, large size, network issues) are shown immediately on-screen.

- **📦 Dockerized Deployment**  
  The entire stack runs with a single command using Docker Compose.

---

## ⚙️ Installation

Clone the repository and start the containers:

```bash
git clone https://github.com/wspjoy2011/upload-server.git
cd upload-server
docker-compose up --build
```

Before running the server, configure the environment variables for the backend:

1. Navigate to the backend service directory:
   ```bash
   cd services/backend
   ```

2. Copy the sample file and adjust the values as needed:
   ```bash
   cp .env.sample .env
   ```

3. Sample `.env.sample`:

   ```env
   # Directory where uploaded images will be stored 
   IMAGES_DIR=/usr/src/images

   # Directory where log files will be written
   LOG_DIR=/var/log

   # Number of worker processes to spawn for HTTP server
   WEB_SERVER_WORKERS=10

   # Starting port number for worker processes (each worker gets a unique port)
   WEB_SERVER_START_PORT=8000
   ```

Make sure the `IMAGES_DIR` and `LOG_DIR` match the volume paths defined in `docker-compose.yml`.

Then visit:  
[http://localhost](http://localhost)

---

## 📂 Usage

### Web UI

1. Open the browser and go to `http://localhost`
2. Drag and drop or select a file to upload
3. Copy the generated image URL
4. Switch to the "Images" tab to see all uploaded files
5. Click the trash icon to delete any file

---

## 📁 Project Structure

```
.
├── README.md
├── docker-compose.yml
├── images/                      # Uploaded files stored here (mounted volume)
├── logs/
│   ├── app.log                  # Backend logs
│   └── nginx/
│       ├── access.log
│       └── error.log
└── services/
    ├── backend/
    │   ├── Dockerfile
    │   ├── poetry.lock
    │   ├── pyproject.toml
    │   └── src/
    │       ├── app.py
    │       ├── exceptions/
    │       │   └── api_errors.py
    │       ├── handlers/
    │       │   ├── files.py
    │       │   └── upload.py
    │       ├── interfaces/
    │       │   └── protocols.py
    │       └── settings/
    │           ├── config.py
    │           └── logging_config.py
    ├── frontend/
    │   ├── index.html
    │   ├── upload.html
    │   ├── css/
    │   │   ├── styles.css
    │   │   └── upload.css
    │   ├── js/
    │   │   ├── upload.js
    │   │   ├── tabs.js
    │   │   └── random-hero.js
    │   ├── assets/
    │       ├── ico/
    │       │   └── fav.png
    │       └── images/
    │           ├── 1.png ... 5.png
    └── nginx/
        └── nginx.conf
```

---

## 🧰 Tech Stack

| Layer     | Technology                 |
|-----------|----------------------------|
| Backend   | Python `http.server`, custom routing |
| Frontend  | HTML, CSS, JavaScript      |
| Web Server| Nginx                      |
| Logging   | Python Logging + Nginx logs|
| Packaging | Docker, Docker Compose     |
| Styling   | Custom CSS (no frameworks) |

---

## ✅ License

MIT License. Use freely, fork, or extend.
