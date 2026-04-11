# 🚀 Production Deployment Guide

## Steps to Deploy on Server

---

## Method 1: Docker (Recommended) 🐳

### Step 1: Upload Files to Server
```bash
# Copy from local to server
scp -r Face_attendance_professional user@your-server-ip:/path/
```

### Step 2: Start Docker Compose
```bash
cd Face_attendance_professional
docker-compose up -d
```

**Services:**
- MySQL: Port 3306
- Backend: Port 8000
- Frontend: Built-in in backend

### Step 3: Create Admin User
```bash
curl -X POST http://localhost:8000/auth/setup-admin \
  -d "username=admin@gmail.com&password=admin123"
```

**Access:** `http://your-server-ip:8000/`

---

## Method 2: Manual Server Setup

### Install Requirements
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3-pip python3-venv mysql-server nginx

# MySQL secure installation
sudo mysql_secure_installation
```

### MySQL Setup
```bash
sudo mysql -u root -p

# Run these commands in MySQL:
CREATE DATABASE IF NOT EXISTS face_attendance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'faceapp'@'localhost' IDENTIFIED BY 'faceapp123';
GRANT ALL PRIVILEGES ON face_attendance.* TO 'faceapp'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Application Setup
```bash
cd Face_attendance_professional

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Environment variables
nano .env
```

**`.env` content:**
```
DATABASE_URL=mysql+pymysql://faceapp:faceapp123@localhost:3306/face_attendance
SECRET_KEY=your-super-secret-key-here
```

### Start Application
```bash
python main.py
```

---

## Nginx Configuration (Production)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/face-attendance /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔐 Security Checklist

- [ ] Change `SECRET_KEY`: `openssl rand -hex 32`
- [ ] Set strong MySQL password
- [ ] Open only required ports in firewall (80, 443, 8000)
- [ ] Enable HTTPS (Let's Encrypt)
- [ ] Secure `.env` file (chmod 600)

---

## 🌐 SSL/HTTPS Setup (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `.env` | Database credentials & secrets |
| `docker-compose.yml` | Docker services config |
| `Dockerfile` | Backend container |
| `uploads/` | Student photos (backup required!) |
| `data/` | Cache files |

---

## 🔄 Auto Start (Systemd)

Create `/etc/systemd/system/face-attendance.service`:

```ini
[Unit]
Description=Face Attendance Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Face_attendance_professional
Environment="PATH=/home/ubuntu/Face_attendance_professional/venv/bin"
Environment="DATABASE_URL=mysql+pymysql://faceapp:faceapp123@localhost:3306/face_attendance"
ExecStart=/home/ubuntu/Face_attendance_professional/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable face-attendance
sudo systemctl start face-attendance
```

---

## 🔗 URLs After Deployment

| Service | URL |
|---------|-----|
| Login Page | `http://your-server-ip:8000/` |
| API Docs | `http://your-server-ip:8000/docs` |
| Backend API | `http://your-server-ip:8000/` |

---

## 🆘 Troubleshooting

### MySQL Connection Error
```bash
# Check MySQL status
sudo systemctl status mysql

# Start MySQL
sudo systemctl start mysql
```

### Port Already in Use
```bash
# Check port 8000
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

---

**Server Ready!** 🎉
