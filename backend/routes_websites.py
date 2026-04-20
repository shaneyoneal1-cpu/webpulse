from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from datetime import datetime, timezone, timedelta
from database import get_db
from models import Website, CheckResult, User
from schemas import WebsiteCreate, WebsiteResponse, CheckResultResponse, DashboardStats, WeeklyRoundup
from auth import get_current_user, check_permission
from monitor import check_website
from config import MAX_WEBSITES
import random

router = APIRouter(prefix="/api/websites", tags=["websites"])

PERFORMANCE_TIPS = [
    "Enable HTTP/2 on your web server for multiplexed connections and header compression.",
    "Use WebP or AVIF image formats for 30-50% smaller file sizes without quality loss.",
    "Implement lazy loading for images below the fold to speed up initial page render.",
    "Set up a Content Delivery Network (CDN) to serve assets from edge locations.",
    "Enable Brotli compression on your server - it's 15-25% more efficient than gzip.",
    "Minimize render-blocking CSS and JS by deferring non-critical resources.",
    "Use preconnect hints for third-party domains to reduce DNS/TLS overhead.",
    "Implement service workers for offline caching and faster repeat visits.",
    "Optimize your Critical Rendering Path by inlining above-the-fold CSS.",
    "Consider using a headless CMS or static site generator for content-heavy pages.",
    "Monitor your Core Web Vitals (LCP, FID, CLS) for real user experience metrics.",
    "Database query optimization can reduce TTFB by 40-60% for dynamic pages.",
]


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    websites = db.query(Website).filter(Website.is_active == True).all()
    total = len(websites)
    up = 0
    down = 0
    latencies = []
    load_times = []

    for w in websites:
        latest = db.query(CheckResult).filter(
            CheckResult.website_id == w.id
        ).order_by(desc(CheckResult.checked_at)).first()
        if latest:
            if latest.is_up:
                up += 1
            else:
                down += 1
            if latest.latency_ms:
                latencies.append(latest.latency_ms)
            if latest.page_load_time_ms:
                load_times.append(latest.page_load_time_ms)
        else:
            up += 1

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    total_checks = db.query(CheckResult).filter(CheckResult.checked_at >= week_ago).count()
    up_checks = db.query(CheckResult).filter(
        CheckResult.checked_at >= week_ago, CheckResult.is_up == True
    ).count()
    uptime = round((up_checks / total_checks * 100), 2) if total_checks > 0 else None

    return DashboardStats(
        total_websites=total,
        websites_up=up,
        websites_down=down,
        avg_latency=round(sum(latencies) / len(latencies), 2) if latencies else None,
        avg_page_load=round(sum(load_times) / len(load_times), 2) if load_times else None,
        uptime_percentage=uptime,
    )


@router.get("/weekly-roundup", response_model=WeeklyRoundup)
def get_weekly_roundup(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    this_week = db.query(CheckResult).filter(CheckResult.checked_at >= week_ago).all()
    last_week = db.query(CheckResult).filter(
        CheckResult.checked_at >= two_weeks_ago, CheckResult.checked_at < week_ago
    ).all()

    tw_latencies = [c.latency_ms for c in this_week if c.latency_ms]
    lw_latencies = [c.latency_ms for c in last_week if c.latency_ms]
    tw_speeds = [c.page_load_time_ms for c in this_week if c.page_load_time_ms]
    lw_speeds = [c.page_load_time_ms for c in last_week if c.page_load_time_ms]

    avg_latency_change = None
    if tw_latencies and lw_latencies:
        avg_latency_change = round(
            (sum(tw_latencies) / len(tw_latencies)) - (sum(lw_latencies) / len(lw_latencies)), 2
        )

    avg_speed_change = None
    if tw_speeds and lw_speeds:
        avg_speed_change = round(
            (sum(tw_speeds) / len(tw_speeds)) - (sum(lw_speeds) / len(lw_speeds)), 2
        )

    up_checks = len([c for c in this_week if c.is_up])
    uptime = round((up_checks / len(this_week) * 100), 2) if this_week else None

    websites = db.query(Website).filter(Website.is_active == True).all()
    improved = 0
    degraded = 0
    for w in websites:
        tw = [c for c in this_week if c.website_id == w.id and c.page_load_time_ms]
        lw = [c for c in last_week if c.website_id == w.id and c.page_load_time_ms]
        if tw and lw:
            tw_avg = sum(c.page_load_time_ms for c in tw) / len(tw)
            lw_avg = sum(c.page_load_time_ms for c in lw) / len(lw)
            if tw_avg < lw_avg:
                improved += 1
            elif tw_avg > lw_avg:
                degraded += 1

    return WeeklyRoundup(
        avg_latency_change=avg_latency_change,
        avg_speed_change=avg_speed_change,
        uptime_percentage=uptime,
        total_checks=len(this_week),
        sites_improved=improved,
        sites_degraded=degraded,
        tip=random.choice(PERFORMANCE_TIPS),
    )


@router.get("", response_model=List[WebsiteResponse])
def list_websites(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not check_permission(user, "view_websites"):
        raise HTTPException(status_code=403, detail="Permission denied")

    websites = db.query(Website).all()
    results = []
    for w in websites:
        latest = db.query(CheckResult).filter(
            CheckResult.website_id == w.id
        ).order_by(desc(CheckResult.checked_at)).first()

        latest_dict = None
        if latest:
            latest_dict = {
                "is_up": latest.is_up,
                "latency_ms": latest.latency_ms,
                "page_load_time_ms": latest.page_load_time_ms,
                "status_code": latest.status_code,
                "checked_at": latest.checked_at.isoformat() if latest.checked_at else None,
            }

        results.append(WebsiteResponse(
            id=w.id, url=w.url, name=w.name, is_active=w.is_active,
            created_at=w.created_at, latest_check=latest_dict,
        ))
    return results


@router.post("", response_model=WebsiteResponse)
def add_website(
    site: WebsiteCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not check_permission(user, "manage_websites"):
        raise HTTPException(status_code=403, detail="Permission denied")

    count = db.query(Website).count()
    if count >= MAX_WEBSITES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_WEBSITES} websites allowed")

    website = Website(url=site.url, name=site.name, created_by=user.id)
    db.add(website)
    db.commit()
    db.refresh(website)
    return WebsiteResponse(id=website.id, url=website.url, name=website.name,
                           is_active=website.is_active, created_at=website.created_at)


@router.delete("/{website_id}")
def delete_website(
    website_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not check_permission(user, "manage_websites"):
        raise HTTPException(status_code=403, detail="Permission denied")

    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    db.delete(website)
    db.commit()
    return {"message": "Website deleted"}


@router.post("/{website_id}/check")
async def check_now(
    website_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not check_permission(user, "run_checks"):
        raise HTTPException(status_code=403, detail="Permission denied")

    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    result = await check_website(website.url)
    check = CheckResult(
        website_id=website.id,
        is_up=result["is_up"],
        status_code=result["status_code"],
        latency_ms=result["latency_ms"],
        page_load_time_ms=result["page_load_time_ms"],
        page_size_kb=result["page_size_kb"],
        ttfb_ms=result["ttfb_ms"],
        suggestions=result["suggestions"],
        error_message=result["error_message"],
    )
    db.add(check)
    db.commit()
    db.refresh(check)

    return CheckResultResponse(
        id=check.id, website_id=check.website_id, is_up=check.is_up,
        status_code=check.status_code, latency_ms=check.latency_ms,
        page_load_time_ms=check.page_load_time_ms, page_size_kb=check.page_size_kb,
        ttfb_ms=check.ttfb_ms, suggestions=check.suggestions,
        error_message=check.error_message, checked_at=check.checked_at
    )


@router.get("/{website_id}/history", response_model=List[CheckResultResponse])
def get_history(
    website_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not check_permission(user, "view_websites"):
        raise HTTPException(status_code=403, detail="Permission denied")

    results = db.query(CheckResult).filter(
        CheckResult.website_id == website_id
    ).order_by(desc(CheckResult.checked_at)).limit(50).all()
    return results
