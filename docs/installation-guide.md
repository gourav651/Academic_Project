# Installation & Setup Guide

This guide details steps to set up and run the autonomous software engineering framework locally.

---

## Prerequisites

1. **Python 3.11 - 3.14**
2. **Node.js (v18+) & npm**
3. **Docker Desktop** (Optional, recommended for safe containerized code execution)
4. **Ollama** (Free local open-source LLM inference engine)

---

## Step 1: Install & Configure Ollama

1. Download Ollama from [https://ollama.com](https://ollama.com).
2. Install and launch the Ollama service:
   ```bash
   ollama serve
   ```
3. Pull a lightweight coding model suitable for your hardware:
   - For 8 GB RAM / 4 GB GPU VRAM (Recommended):
     ```bash
     ollama pull qwen2.5-coder:1.5b
     ```
   - For higher capability:
     ```bash
     ollama pull qwen2.5-coder:3b
     ```

---

## Step 2: Backend Setup

1. Open a terminal in the `backend/` directory:
   ```bash
   cd d:\MINOR_PROJECT\backend
   ```
2. Activate the Python virtual environment:
   ```bash
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Verify tests pass:
   ```bash
   python -m pytest tests -v
   ```
5. Start the FastAPI development server:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Interactive API docs are available at `http://localhost:8000/docs`.

---

## Step 3: Frontend Setup

1. Open a separate terminal in the `frontend/` directory:
   ```bash
   cd d:\MINOR_PROJECT\frontend
   ```
2. Install dependencies (if not already installed):
   ```bash
   npm install --legacy-peer-deps
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to `http://localhost:5173`.
