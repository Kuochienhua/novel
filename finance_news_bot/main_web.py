from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, Subscriber, init_db
import uvicorn

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化資料庫
init_db()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/subscribe", response_class=HTMLResponse)
async def subscribe(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    # Check if email exists
    existing_user = db.query(Subscriber).filter(Subscriber.email == email).first()
    if existing_user:
        if not existing_user.is_active:
            existing_user.is_active = True
            db.commit()
            return templates.TemplateResponse("index.html", {"request": request, "message": "歡迎回來！您已重新訂閱成功。", "status": "success"})
        return templates.TemplateResponse("index.html", {"request": request, "message": "這個 Email 已經訂閱過囉！", "status": "warning"})
    
    # Create new subscriber
    new_subscriber = Subscriber(email=email)
    db.add(new_subscriber)
    db.commit()
    
    return templates.TemplateResponse("index.html", {"request": request, "message": "訂閱成功！謝謝您的支持。", "status": "success"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
