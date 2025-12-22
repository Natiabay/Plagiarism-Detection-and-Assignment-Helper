# Correct WSL and Docker Commands

## Issue: `wsl --status` Not Working

The `wsl --status` command must be run from **Windows PowerShell**, not from inside WSL/Ubuntu.

---

## Correct Commands

### From Windows PowerShell (Not WSL)

Open **PowerShell** (not WSL/Ubuntu terminal) and run:

```powershell
# Check WSL status
wsl --status

# List WSL distributions
wsl --list --verbose

# Check WSL version
wsl --version
```

### From WSL/Ubuntu Terminal

If you're inside WSL, use these commands instead:

```bash
# Check if you're in WSL
cat /proc/version

# Check Linux distribution
lsb_release -a

# Check Docker (if installed in WSL)
docker --version

# Exit WSL to go back to Windows
exit
```

---

## Check Docker Status

### From Windows PowerShell

```powershell
# Check if Docker is running
docker --version

# Check Docker containers
docker ps

# Check Docker Compose
docker-compose ps

# Check all services
docker-compose ps
```

### From WSL/Ubuntu

If Docker is installed in WSL:

```bash
# Check Docker
docker --version

# Check containers
docker ps

# But note: Docker Desktop on Windows manages containers
# You may need to access them from Windows PowerShell
```

---

## Fix Docker Connection Issue

### Step 1: Open Windows PowerShell (Not WSL)

Press `Win + X` and select "Windows PowerShell" or "Terminal"

### Step 2: Navigate to Project Directory

```powershell
cd "C:\Users\HP\Desktop\Academic Assignment Helper and plagiarism detector(RAG )"
```

### Step 3: Check Docker Desktop

1. **Open Docker Desktop** application
2. **Wait for it to start** (whale icon in system tray)
3. **Verify it shows "Docker Desktop is running"**

### Step 4: Check Services

```powershell
# Check if containers are running
docker ps

# If no containers, start them
docker-compose up -d

# Wait 30 seconds
Start-Sleep -Seconds 30

# Check again
docker ps
```

### Step 5: Test PostgreSQL

```powershell
# Test database connection
docker exec academic_postgres psql -U student -d academic_helper -c "SELECT 1;"
```

---

## Common Commands Reference

### Windows PowerShell Commands

```powershell
# WSL Management
wsl --status                    # Check WSL status
wsl --list --verbose           # List distributions
wsl --set-default-version 2    # Set default version
wsl --update                   # Update WSL

# Docker Commands
docker --version               # Check Docker version
docker ps                      # List running containers
docker-compose ps              # List compose services
docker-compose up -d           # Start services
docker-compose down            # Stop services
docker-compose logs postgres   # View logs
docker exec academic_postgres psql -U student -d academic_helper -c "SELECT 1;"
```

### WSL/Ubuntu Commands

```bash
# System Info
uname -a                       # System information
lsb_release -a                 # Distribution info
cat /proc/version              # Kernel version

# Exit to Windows
exit                           # Exit WSL

# Docker (if installed)
docker --version
docker ps
```

---

## Quick Fix for Your Situation

Since you're in WSL, here's what to do:

### Option 1: Exit WSL and Use Windows PowerShell

```bash
# Exit WSL
exit
```

Then open **Windows PowerShell** and run:

```powershell
# Navigate to project
cd "C:\Users\HP\Desktop\Academic Assignment Helper and plagiarism detector(RAG )"

# Check Docker
docker ps

# Start services if needed
docker-compose up -d
```

### Option 2: Use Docker from WSL (If Configured)

If Docker Desktop is configured for WSL integration:

```bash
# Check Docker
docker --version

# If Docker works, you can use it
docker ps
docker-compose ps
```

---

## Verify Docker Desktop WSL Integration

1. **Open Docker Desktop**
2. **Go to Settings** (gear icon)
3. **Resources → WSL Integration**
4. **Enable integration** with your Ubuntu distribution
5. **Click "Apply & Restart"**

After this, Docker commands should work from WSL.

---

## Test n8n Connection After Docker is Running

Once Docker services are running (from Windows PowerShell):

1. **Open n8n**: http://localhost:5678
2. **Open Postgres credential**
3. **Click "Retry"**
4. **Should connect successfully!**

---

## Summary

- ✅ `wsl --status` must be run from **Windows PowerShell**, not WSL
- ✅ Docker commands work from **Windows PowerShell**
- ✅ If Docker Desktop has WSL integration enabled, Docker commands also work from WSL
- ✅ For your n8n connection issue, make sure Docker services are running first

**Next Step**: Exit WSL, open Windows PowerShell, and run `docker ps` to check if services are running.

