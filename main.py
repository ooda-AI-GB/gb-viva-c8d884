import os
import uvicorn
from datetime import datetime
from typing import List

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base

# --- Configuration & Database ---
os.makedirs("data", exist_ok=True)
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Models ---
class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    attendees = relationship("Attendee", back_populates="meeting")

class Attendee(Base):
    __tablename__ = "attendees"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    name = Column(String)
    hourly_rate = Column(Float)

    meeting = relationship("Meeting", back_populates="attendees")

# --- App Setup ---
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meeting Cost Ticker")
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Routes ---

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def root(db: Session = Depends(get_db)):
    active_meeting = db.query(Meeting).filter(Meeting.is_active == True).first()
    if active_meeting:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/setup")

@app.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request, db: Session = Depends(get_db)):
    active_meeting = db.query(Meeting).filter(Meeting.is_active == True).first()
    if active_meeting:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("setup.html", {"request": request})

@app.post("/start")
def start_meeting(
    names: List[str] = Form(...),
    rates: List[float] = Form(...),
    db: Session = Depends(get_db)
):
    # Filter out empty entries if any
    valid_entries = []
    for n, r in zip(names, rates):
        if n.strip() and r >= 0:
            valid_entries.append((n, r))
            
    if not valid_entries:
         return RedirectResponse(url="/setup", status_code=303)

    new_meeting = Meeting(start_time=datetime.now(), is_active=True)
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)

    for name, rate in valid_entries:
        attendee = Attendee(meeting_id=new_meeting.id, name=name, hourly_rate=rate)
        db.add(attendee)
    
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.is_active == True).first()
    if not meeting:
        return RedirectResponse(url="/")
    
    total_hourly_rate = sum(a.hourly_rate for a in meeting.attendees)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "meeting": meeting,
        "attendees": meeting.attendees,
        "start_time_ts": meeting.start_time.timestamp(),
        "total_hourly_rate": total_hourly_rate
    })

@app.post("/stop")
def stop_meeting(db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.is_active == True).first()
    if meeting:
        meeting.is_active = False
        meeting.end_time = datetime.now()
        db.commit()
        return RedirectResponse(url=f"/summary/{meeting.id}", status_code=303)
    return RedirectResponse(url="/", status_code=303)

@app.get("/summary/{meeting_id}", response_class=HTMLResponse)
def summary(meeting_id: int, request: Request, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Calculate duration
    start = meeting.start_time
    end = meeting.end_time or datetime.now() # Fallback if viewing active meeting summary
    duration = end - start
    duration_seconds = duration.total_seconds()
    
    hours, remainder = divmod(duration_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    duration_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

    # Calculate cost
    total_hourly_rate = sum(a.hourly_rate for a in meeting.attendees)
    total_cost = (duration_seconds / 3600) * total_hourly_rate

    return templates.TemplateResponse("summary.html", {
        "request": request,
        "meeting": meeting,
        "duration_str": duration_str,
        "total_cost": total_cost,
        "attendee_count": len(meeting.attendees)
    })

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
