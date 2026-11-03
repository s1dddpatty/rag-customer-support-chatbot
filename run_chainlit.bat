@echo off
echo ===================================================
echo Starting Chainlit UI on http://localhost:8502
echo ===================================================
.\venv\Scripts\chainlit.exe run ui/chainlit_app.py --port 8502 -w
pause

