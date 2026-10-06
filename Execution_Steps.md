# Enterprise RAG - Execution Commands Guide

Follow these exact commands step-by-step to run the project on a new laptop.

---

## 0. Prerequisites Check

Check that Python and Node.js are installed on your laptop:

```bash
python --version
node -v
npm -v
```
*(Requires Python 3.10+ and Node.js 18+)*

---

## 1. Setup Environment Configuration

Open a terminal, navigate inside the project folder, and create the `.env` file:

### Windows (PowerShell or CMD)
```powershell
copy .env.example .env
```

### macOS / Linux
```bash
cp .env.example .env
```

> **Note**: Open `.env` and set your `LLM_API_KEY`:
> ```env
> LLM_API_KEY=gsk_your_groq_api_key_here
> ```

---

## 2. Terminal 1: Backend Setup & Run

Open **Terminal 1** in the root `enterprise_rag` directory:

### On Windows (PowerShell / Command Prompt)
```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### On macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

> Backend will start running at: **`http://127.0.0.1:8000`**  
> API Docs available at: **`http://127.0.0.1:8000/docs`**

---

## 3. Terminal 2: Frontend Setup & Run

Open a **new second terminal (Terminal 2)** in the root `enterprise_rag` directory:

### Windows / macOS / Linux
```bash
cd frontend
npm install
npm run dev
```

> Frontend will start running at: **`http://localhost:5173`**

---

## 4. (Optional) Rebuild Document Indexes

If you ever add new documents or need to re-index documents from scratch, run in Terminal 1 (with virtual environment activated):

```bash
python -m scripts.ingest
```

---

## 5. Open Web Application & Login

Open your web browser and go to:
👉 **`http://localhost:5173`**

### Demo Login Accounts:
| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@acme.local` | `AdminMaster@Acme2026!` |
| **Employee** | `employee@acme.local` | `Employee@Acme2026!` |
| **HR** | `hr@acme.local` | `HRAdmin@Acme2026!` |
| **Finance** | `finance@acme.local` | `Finance@Acme2026!` |
| **Security** | `security@acme.local` | `SecuritySec@Acme2026!` |
