import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


XOTELO_API_HOST = "xotelo-hotel-prices.p.rapidapi.com"
XOTELO_BASE_URL = f"https://{XOTELO_API_HOST}/api"
REPO_ROOT = Path(__file__).resolve().parents[2]
XOTELO_ENV_PATH = REPO_ROOT / "services/search-api/.env"
OUTPUT_ROOT = REPO_ROOT / "resources/policy_pdfs"


HOTELS: List[Dict[str, Any]] = [
    {
        "name": "Rosewood Hotel de Crillon",
        "policy_url": "https://www.rosewoodhotels.com/en/hotel-de-crillon/hotel-policies",
    },
    {
        "name": "Four Seasons Hotel George V",
        "policy_url": "https://www.fourseasons.com/paris/",
    },
    {
        "name": "Le Bristol Paris",
        "policy_url": "https://www.lebristolparis.com/",
    },
    {
        "name": "The Ritz Paris",
        "policy_url": "https://www.ritzparis.com/en-GB",
    },
    {
        "name": "Le Burgundy Paris",
        "policy_url": "https://www.leburgundy.com/",
    },
    {
        "name": "L'Hotel Paris",
        "policy_url": "https://www.l-hotel.com/reservation-policy/",
    },
    {
        "name": "Hotel du Cadran",
        "policy_url": "https://www.cadranhotel.com/blog/en/our-free-cancellation-policy/",
    },
    {
        "name": "Hotel B55",
        "policy_url": "https://www.hotelb55.com/blog/en/booking-with-free-cancellation-in-paris/",
    },
    {
        "name": "Le Citizen Hotel",
        "policy_url": "https://lecitizenhotel.com/en/politique-dannulation-flexible/",
    },
    {
        "name": "Hotel Minerve",
        "policy_url": "https://www.hotel-paris-minerve.com/",
    },
    {
        "name": "Hotel Pavillon Bastille",
        "policy_url": "https://www.pavillonbastille.com/",
    },
    {
        "name": "Mercure Paris Centre Tour Eiffel",
        "policy_url": "https://www.accor.com/",
    },
    {
        "name": "Ibis Paris Bastille Opera",
        "policy_url": "https://www.accor.com/",
    },
    {
        "name": "Holiday Inn Paris Gare de l'Est",
        "policy_url": "https://www.ihg.com/",
    },
    {
        "name": "Novotel Paris Les Halles",
        "policy_url": "https://www.accor.com/",
    },
    {
        "name": "Hotel Paradis Paris",
        "policy_url": "https://hotelparadisparis.com/en/page/hotel-paradis-paris-terms-and-conditions-of-sale-tcs.24126.html",
    },
    {
        "name": "La Reserve Paris",
        "policy_url": "https://www.lareserve-paris.com/en/general-terms-and-conditions/",
    },
    {
        "name": "Warwick Paris",
        "policy_url": "https://www.warwickhotels.com/warwick-paris/terms-and-conditions-of-services",
    },
    {
        "name": "The Hoxton Paris",
        "policy_url": "https://thehoxton.com/paris/terms/",
    },
    {
        "name": "Hotel Charles V",
        "policy_url": "https://www.hotelcharlesv.fr/en/general-terms-and-conditions-of-sale/",
    },
    {
        "name": "Hotel Paris Neuilly",
        "policy_url": "https://www.hotel-paris-neuilly.com/en/terms-and-conditions-of-sale/",
    },
]


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value.lower()).strip("_")
    return slug or "hotel"


def _load_xotelo_api_key() -> str:
    load_dotenv(dotenv_path=XOTELO_ENV_PATH)
    api_key = os.getenv("XOTELO_API_KEY", "")
    if not api_key:
        raise RuntimeError(f"Missing XOTELO_API_KEY in {XOTELO_ENV_PATH}")
    return api_key


def _xotelo_search(api_key: str, hotel_name: str) -> Tuple[str, str]:
    response = requests.get(
        f"{XOTELO_BASE_URL}/search",
        headers={
            "x-rapidapi-host": XOTELO_API_HOST,
            "x-rapidapi-key": api_key,
        },
        params={"query": hotel_name, "location_type": "accommodation"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise RuntimeError(f"Xotelo error for {hotel_name}: {payload.get('error')}")
    results = payload.get("result", {}).get("list", []) or []
    if not results:
        raise RuntimeError(f"No Xotelo results for {hotel_name}")

    def score(item: Dict[str, Any]) -> float:
        candidate = str(item.get("name") or "").lower()
        target = hotel_name.lower()
        if candidate == target:
            return 1.0
        return _similarity(candidate, target)

    best = max(results, key=score)
    return str(best.get("hotel_key") or ""), str(best.get("name") or hotel_name)


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    matches = sum(1 for ch in a if ch in b)
    return matches / max(len(a), len(b))


def _download_pdf(url: str, output_path: Path) -> bool:
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "").lower()
    if "application/pdf" not in content_type and not url.lower().endswith(".pdf"):
        return False
    with output_path.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                handle.write(chunk)
    return True


def _find_pdf_link(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.lower().endswith(".pdf"):
            return urljoin(base_url, href)
    return None


def _extract_policy_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style", "nav", "header", "footer"]):
        node.decompose()
    selectors = [
        "main",
        "article",
        "[role='main']",
        ".content",
        ".policy-content",
        "#content",
        ".main-content",
    ]
    text = ""
    for selector in selectors:
        content = soup.select_one(selector)
        if content:
            text = content.get_text(separator="\n", strip=True)
            break
    if not text:
        text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n\n".join(lines)


def _write_pdf_from_text(text: str, output_path: Path, hotel_name: str) -> None:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="PolicyText",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            spaceAfter=12,
        )
    )
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    story: List[Any] = []
    story.append(Paragraph(f"{hotel_name} - Hotel Policies", styles["Heading1"]))
    story.append(Spacer(1, 0.2 * inch))
    for para in text.split("\n\n"):
        if para.strip():
            cleaned = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(cleaned, styles["PolicyText"]))
            story.append(Spacer(1, 0.1 * inch))
    doc.build(story)


def _create_placeholder_pdf(output_path: Path, hotel_name: str, policy_url: Optional[str]) -> None:
    url_text = policy_url or "Policy URL not provided."
    text = f"Policy information for {hotel_name}.\n\n{url_text}"
    _write_pdf_from_text(text, output_path, hotel_name)


def _process_hotel(api_key: str, hotel: Dict[str, Any]) -> None:
    hotel_name = hotel["name"]
    policy_url = hotel.get("policy_url")
    slug = _slugify(hotel_name)
    hotel_folder = OUTPUT_ROOT / slug
    hotel_folder.mkdir(parents=True, exist_ok=True)

    hotel_id, canonical_name = _xotelo_search(api_key, hotel_name)

    pdf_path = hotel_folder / "policies.pdf"
    if policy_url:
        try:
            downloaded = _download_pdf(policy_url, pdf_path)
            if not downloaded:
                response = requests.get(policy_url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                pdf_link = _find_pdf_link(soup, policy_url)
                if pdf_link and _download_pdf(pdf_link, pdf_path):
                    pass
                else:
                    policy_text = _extract_policy_text(response.text)
                    if not policy_text:
                        _create_placeholder_pdf(pdf_path, canonical_name, policy_url)
                    else:
                        _write_pdf_from_text(policy_text, pdf_path, canonical_name)
        except Exception:
            _create_placeholder_pdf(pdf_path, canonical_name, policy_url)
    else:
        _create_placeholder_pdf(pdf_path, canonical_name, policy_url)

    metadata_path = hotel_folder / "metadata.json"
    metadata = {"hotelId": hotel_id, "hotelName": canonical_name}
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    api_key = _load_xotelo_api_key()
    for hotel in HOTELS:
        _process_hotel(api_key, hotel)
        time.sleep(1)


if __name__ == "__main__":
    main()
