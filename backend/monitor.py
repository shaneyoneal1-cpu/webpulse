import httpx
import time
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Website, CheckResult

logger = logging.getLogger("webpulse.monitor")


def generate_suggestions(result: dict) -> list:
    suggestions = []
    latency = result.get("latency_ms")
    load_time = result.get("page_load_time_ms")
    page_size = result.get("page_size_kb")
    ttfb = result.get("ttfb_ms")

    if latency and latency > 500:
        suggestions.append({
            "type": "latency",
            "severity": "high" if latency > 1000 else "medium",
            "message": f"High latency detected ({latency:.0f}ms). Consider using a CDN or moving servers closer to your users."
        })
    if ttfb and ttfb > 800:
        suggestions.append({
            "type": "ttfb",
            "severity": "high" if ttfb > 1500 else "medium",
            "message": f"Slow Time to First Byte ({ttfb:.0f}ms). Optimize server-side processing, enable caching, or upgrade hosting."
        })
    if load_time and load_time > 3000:
        suggestions.append({
            "type": "page_speed",
            "severity": "high" if load_time > 5000 else "medium",
            "message": f"Page load time is {load_time:.0f}ms. Optimize images, minify CSS/JS, and enable compression."
        })
    if page_size and page_size > 2000:
        suggestions.append({
            "type": "page_size",
            "severity": "high" if page_size > 5000 else "medium",
            "message": f"Large page size ({page_size:.0f}KB). Compress assets, lazy-load images, and remove unused code."
        })
    if page_size and page_size > 500 and page_size <= 2000:
        suggestions.append({
            "type": "page_size",
            "severity": "low",
            "message": "Consider optimizing images with WebP format and enabling Brotli compression."
        })
    if load_time and load_time <= 1500 and latency and latency <= 200:
        suggestions.append({
            "type": "performance",
            "severity": "info",
            "message": "Great performance! Keep monitoring to maintain these speeds."
        })
    if not suggestions:
        suggestions.append({
            "type": "general",
            "severity": "info",
            "message": "Performance looks acceptable. Consider implementing HTTP/2, preloading critical resources, and using service workers for caching."
        })
    return suggestions


async def check_website(url: str) -> dict:
    result = {
        "is_up": False,
        "status_code": None,
        "latency_ms": None,
        "page_load_time_ms": None,
        "page_size_kb": None,
        "ttfb_ms": None,
        "error_message": None,
        "suggestions": [],
    }
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            start = time.monotonic()
            response = await client.get(url)
            total_time = (time.monotonic() - start) * 1000

            result["is_up"] = response.status_code < 500
            result["status_code"] = response.status_code
            result["page_load_time_ms"] = round(total_time, 2)

            elapsed = response.elapsed
            result["ttfb_ms"] = round(elapsed.total_seconds() * 1000, 2)
            result["latency_ms"] = round(elapsed.total_seconds() * 1000, 2)

            content = response.content
            result["page_size_kb"] = round(len(content) / 1024, 2)

    except httpx.TimeoutException:
        result["error_message"] = "Request timed out after 30 seconds"
    except httpx.ConnectError as e:
        result["error_message"] = f"Connection error: {str(e)[:200]}"
    except Exception as e:
        result["error_message"] = f"Error: {str(e)[:200]}"

    result["suggestions"] = generate_suggestions(result)
    return result


async def run_checks():
    logger.info("Running scheduled website checks...")
    db: Session = SessionLocal()
    try:
        websites = db.query(Website).filter(Website.is_active == True).all()
        for website in websites:
            try:
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
                logger.info(f"Checked {website.name} ({website.url}): up={result['is_up']}, latency={result['latency_ms']}ms")
            except Exception as e:
                logger.error(f"Error checking {website.url}: {e}")
                db.rollback()
    finally:
        db.close()
