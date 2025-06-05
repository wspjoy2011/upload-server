# 📷 Image Hosting Server

A comprehensive containerized service for uploading, viewing, and managing images via a modern browser interface.  
It features a drag-and-drop uploader, image gallery with pagination, detailed image view, automatic URL generation, and persistent logging — all powered by a clean backend + frontend separation with database support and managed with Docker Compose.

---

## ✨ Table of Contents

- [Overview](#-overview)
- [Features](#-features)  
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [API Endpoints](#-api-endpoints)

---

## 📌 Overview

This project is a full-featured image hosting service built for uploading, managing, and sharing images through a modern UI.  
It includes:

- A **backend server** written in pure Python (using standard library `http.server` with custom routing)
- A modern **frontend UI** with drag-and-drop support and image gallery  
- **PostgreSQL database** for metadata storage
- **PgBouncer** for connection pooling
- **Nginx reverse proxy** with load balancing
- **Comprehensive logging** of all backend and access events
- RESTful API with routes for uploading, listing, viewing, and deleting images

All components are containerized and orchestrated via `docker-compose`.

---

## 🚀 Features

- **📤 Upload via Drag & Drop or Button**  
  Users can upload `.jpg`, `.png`, or `.gif` images by clicking a button or dragging files into the UI.

- **🖼 Image Gallery with Pagination**  
  Uploaded images are displayed in a beautiful card-based gallery with pagination controls and sorting options.

- **📋 Detailed Image View**  
  Click on any image to view detailed information including metadata, upload date, file size, and more.

- **🔍 Fullscreen Preview**  
  View images in fullscreen mode with smooth transitions and navigation controls.

- **🗑 Delete Support**  
  Each image includes delete functionality with confirmation prompts for safe removal.

- **🔁 Live Tab Switching**  
  The UI allows switching between "Upload" and "Images" views with URL parameter support and localStorage persistence.

- **📱 Responsive Design**  
  Fully responsive interface that works perfectly on desktop, tablet, and mobile devices.

- **🧠 Error Feedback**  
  All user errors (bad type, large size, network issues) are shown immediately with clear messaging.

- **🔄 Real-time Updates**  
  Gallery automatically updates after uploads and deletions without page refresh.

- **📦 Dockerized Deployment**  
  The entire stack runs with a single command using Docker Compose.

---

## ⚙️ Installation

Clone the repository and start the containers:

    git clone https://github.com/wspjoy2011/upload-server.git
    cd upload-server
    docker-compose up --build

Before running the server, configure the environment variables:

**1. Backend Configuration:**

    cd services/backend
    cp .env.sample .env

Edit the `.env` file with your configuration. Sample variables:

    # Directory where uploaded images will be stored
    IMAGES_DIR=/usr/src/images
    # Directory where log files will be written  
    LOG_DIR=/var/log
    
    # Number of worker processes to spawn for HTTP server
    WEB_SERVER_WORKERS=4
    # Starting port number for worker processes
    WEB_SERVER_START_PORT=8000
    
    # PostgreSQL Database Configuration
    POSTGRES_DB=upload_images_db
    POSTGRES_DB_PORT=5432
    POSTGRES_USER=admin
    POSTGRES_PASSWORD=some_password
    POSTGRES_HOST=postgres-upload-server

**2. PgBouncer Configuration:**

    cd services/pgbouncer
    cp .env.sample .env

Edit the `.env` file with your PgBouncer settings:

    # PgBouncer Configuration
    PGBOUNCER_USER=bouncer_user
    PGBOUNCER_PASSWORD=change_this_password_in_prod
    PGBOUNCER_HOST=pgbouncer-upload-server
    PGBOUNCER_PORT=6432
    USE_PGBOUNCER=true
    MAX_CLIENT_CONN=200
    DEFAULT_POOL_SIZE=20

Then visit: **http://localhost**

---

## 📂 Usage

### Web UI

1. **Upload Images:**
   - Open browser and go to `http://localhost`
   - Drag and drop or select files to upload
   - Copy the generated image URLs

2. **Browse Gallery:**
   - Switch to "Images" tab to see all uploaded files
   - Use pagination controls to navigate through images
   - Sort by newest or oldest first
   - Adjust items per page (4, 8, or 12)

3. **View Image Details:**
   - Click on any image to view detailed information
   - See metadata, file size, upload date, and more
   - Use fullscreen mode for better viewing
   - Copy direct URLs or download images

4. **Manage Images:**
   - Delete images with confirmation prompts
   - All changes reflected immediately in gallery

---

## 📁 Project Structure

    .
    ├── README.md
    ├── docker-compose.yml
    ├── .dockerignore
    ├── .gitignore
    ├── images/                      # Uploaded files stored here
    ├── logs/
    │   ├── app.log                  # Backend logs
    │   └── nginx/
    │       ├── access.log
    │       └── error.log
    ├── init-sql/                    # Database initialization scripts
    │   ├── 1-init.sql
    │   ├── 2-create-tables.sql
    │   └── 3-create-indexes.sql
    └── services/
        ├── backend/
        │   ├── Dockerfile
        │   ├── .env.sample
        │   ├── poetry.lock
        │   ├── pyproject.toml
        │   └── src/
        │       ├── main.py
        │       ├── database/
        │       │   ├── __init__.py
        │       │   ├── connection.py
        │       │   └── models.py
        │       ├── dto/
        │       │   ├── __init__.py
        │       │   └── file.py
        │       ├── handlers/
        │       │   ├── __init__.py
        │       │   └── upload.py
        │       ├── services/
        │       │   ├── __init__.py
        │       │   └── image_service.py
        │       └── utils/
        │           ├── __init__.py
        │           ├── config.py
        │           └── logging_config.py
        ├── frontend/
        │   ├── index.html
        │   ├── upload.html
        │   ├── image_detail.html
        │   ├── css/
        │   │   ├── styles.css
        │   │   ├── upload.css
        │   │   └── image_detail.css
        │   ├── js/
        │   │   ├── upload.js
        │   │   ├── tabs.js
        │   │   ├── image_detail.js
        │   │   └── random-hero.js
        │   └── assets/
        │       ├── ico/
        │       │   └── fav.png
        │       └── images/
        │           └── hero-*.png
        ├── nginx/
        │   └── nginx.conf
        └── pgbouncer/
            ├── Dockerfile
            ├── .env.sample
            └── pgbouncer.ini

---

## 🧰 Tech Stack

| Layer       | Technology                           |
|-------------|--------------------------------------|
| Backend     | Pure Python (http.server, multiprocessing)|
| Database    | PostgreSQL, PgBouncer               |
| Frontend    | HTML5, CSS3, Vanilla JavaScript     |
| Web Server  | Nginx (reverse proxy)               |
| Logging     | Python Logging + Nginx logs         |
| Packaging   | Docker, Docker Compose              |
| Styling     | Custom CSS with responsive design    |
| API         | RESTful with JSON responses          |

---

## 🔧 API Endpoints

| Method | Endpoint                    | Description                    |
|--------|-----------------------------|--------------------------------|
| POST   | `/api/upload/`             | Upload new image               |
| GET    | `/api/upload/`             | List all images with pagination|
| GET    | `/api/upload/{filename}`   | Get specific image details     |
| DELETE | `/api/upload/{filename}`   | Delete specific image          |
| GET    | `/images/{filename}`       | Serve image file               |

---

## 🚨 Important Notes

- Change default passwords in production environment
- `IMAGES_DIR` and `LOG_DIR` should match volume mounts in docker-compose.yml
- Database credentials must be consistent across all services
- PgBouncer acts as connection pooler between application and PostgreSQL

---

## ✅ License

MIT License. Use freely, fork, or extend.
