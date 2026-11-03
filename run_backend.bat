@echo off
echo ===================================================
echo Starting FastAPI Backend on http://127.0.0.1:8000
echo Swagger Docs: http://127.0.0.1:8000/docs
echo ===================================================
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause

