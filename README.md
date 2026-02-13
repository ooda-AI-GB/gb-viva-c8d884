# Meeting Cost Ticker

A real-time meeting cost tracker built with FastAPI, SQLite, and Jinja2. This application visualizes the burning cost of meetings to encourage efficiency.

## Features

- **Setup:** Configure meeting attendees and their hourly rates.
- **Real-time Dashboard:** Watch the cost accumulate second by second.
- **Summary:** View total duration and final cost after the meeting ends.
- **Dockerized:** Ready for deployment.

## Project Structure

This project follows a strict single-file backend architecture:

```
.
├── main.py              # ALL backend code (FastAPI, Models, Routes)
├── requirements.txt     # Dependencies
├── Dockerfile           # Container configuration
├── data/                # Database storage (created at runtime)
└── templates/           # HTML templates
    ├── base.html        # Layout & CSS
    ├── setup.html       # Configuration form
    ├── dashboard.html   # Live tracker
    └── summary.html     # Final report
```

## Running locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python main.py
   ```

3. Open your browser to `http://localhost:8000`.

## Running with Docker

1. Build the image:
   ```bash
   docker build -t meeting-ticker .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 -v $(pwd)/data:/app/data meeting-ticker
   ```
   *Note: The `-v` flag persists the SQLite database.*

3. Open `http://localhost:8000`.

## API Documentation

FastAPI provides automatic API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
