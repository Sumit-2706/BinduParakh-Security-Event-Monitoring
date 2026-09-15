"""Real threat-news endpoint, backed by a live RSS feed (see app/news.py)."""
from fastapi import APIRouter, Depends

from app import models, auth
from app.news import get_threat_news

router = APIRouter(prefix="/news", tags=["news"])


@router.get("")
def list_threat_news(current_user: models.User = Depends(auth.get_current_user)):
    return {"items": get_threat_news()}
