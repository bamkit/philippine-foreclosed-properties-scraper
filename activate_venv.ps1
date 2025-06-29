# Set execution policy only for this session
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# Optional: Print message
Write-Host "✅ Virtual environment activated!" -ForegroundColor Green