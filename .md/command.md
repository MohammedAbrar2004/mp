# whatsapp commands
uvicorn app.api.whatsapp_receiver:app --host 127.0.0.1 --port 8000 --reload
cd api
cd whatsapp
node index.js 

# manual connect endpoint:
python -m uvicorn app.api.whatsapp_receiver:app --host 127.0.0.1 --port 8000

# Text only
1. curl.exe -X POST http://localhost:8001/ingest -F "content=Meeting notes from today"

# PDF only
1. curl.exe -X POST http://localhost:8001/ingest -F "file=@C:\path\to\notes.pdf"
2. curl.exe -X POST http://localhost:8001/ingest -F "content=clash royale rule book" -F "file=@C:\Users\abrar\Downloads\CR1.pdf" 

# DocX only
1. curl.exe -X POST http://localhost:8001/ingest --form "file=@C:\path\to\file.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document"

2. curl.exe -X POST http://localhost:8001/ingest --form "file=@C:\Users\abrar\Downloads\Tech Debate 2026.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document"

3. curl.exe -X POST http://localhost:8001/ingest "content = web dev proposal"--form "file=@C:\Users\abrar\Downloads\Tech Debate 2026.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document"


# Text + audio
curl.exe -X POST http://localhost:8001/ingest --form "content=Voice note" --form "file=@C:\Users\abrar\Downloads\one.ogg;type=audio/ogg"



# Gmail
cd backend
python -m app.connectors.gmail.run_gmail_ingestion


# Calendar
cd backend
python -m app.connectors.calendar.run_calendar_ingestion
