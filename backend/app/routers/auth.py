from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth, detection
from app.notifications import send_alert_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserOut)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # First registered user becomes admin automatically -- convenient for
    # local/first-run setup without a separate seeding script.
    is_first_user = db.query(models.User).count() == 0
    user = models.User(
        email=payload.email,
        hashed_password=auth.hash_password(payload.password),
        role="admin" if is_first_user else "analyst",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        # BinduParakh watches its OWN front door too, not just other
        # people's. A failed dashboard login is logged as a real event
        # (site_id=None means "internal/self") and run through the exact
        # same detection engine -- so someone brute-forcing YOUR
        # dashboard shows up in your own Alerts tab.
        event = models.Event(
            event_type="login_failure",
            identity=form_data.username,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        new_alerts = detection.run_all_rules(db, event)
        for alert in new_alerts:
            send_alert_email(alert.rule_name, alert.severity, alert.description)  # falls back to ALERT_EMAIL_TO

        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = auth.create_access_token(subject=user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
