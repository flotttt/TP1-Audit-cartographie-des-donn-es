import logging
import os
import sys
import time

import requests

METABASE_URL = os.environ.get("METABASE_URL", "http://metabase:3000")
ADMIN_EMAIL = os.environ.get("METABASE_ADMIN_EMAIL", "admin@tp.com")
ADMIN_PASSWORD = os.environ.get("METABASE_ADMIN_PASSWORD", "admin1234")
ADMIN_FIRST = os.environ.get("METABASE_ADMIN_FIRST", "Admin")
ADMIN_LAST = os.environ.get("METABASE_ADMIN_LAST", "TP")
SITE_NAME = os.environ.get("METABASE_SITE_NAME", "TP2 EONET / USGS")

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "db")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("metabase-init")


CARDS = [
    {
        "name": "Total events actifs",
        "display": "scalar",
        "sql": "SELECT COUNT(*) AS events_actifs FROM event WHERE closed IS NULL",
        "size": (6, 3),
    },
    {
        "name": "Total seismes",
        "display": "scalar",
        "sql": "SELECT COUNT(*) AS total_seismes FROM earthquake",
        "size": (6, 3),
    },
    {
        "name": "Magnitude max",
        "display": "scalar",
        "sql": "SELECT MAX(magnitude) AS mag_max FROM earthquake",
        "size": (6, 3),
    },
    {
        "name": "Rapprochements event-seisme",
        "display": "scalar",
        "sql": "SELECT COUNT(*) AS rapprochements FROM event_earthquake",
        "size": (6, 3),
    },
    {
        "name": "Events par categorie",
        "display": "bar",
        "sql": (
            "SELECT c.title AS categorie, COUNT(*) AS nb_events "
            "FROM event_category ec "
            "JOIN category c ON c.id = ec.category_id "
            "GROUP BY c.title "
            "ORDER BY nb_events DESC"
        ),
        "size": (12, 6),
    },
    {
        "name": "Seismes par plage de magnitude",
        "display": "bar",
        "sql": (
            "SELECT FLOOR(magnitude)::text || ' - ' || (FLOOR(magnitude) + 1)::text AS plage, "
            "COUNT(*) AS nb_seismes "
            "FROM earthquake WHERE magnitude IS NOT NULL "
            "GROUP BY FLOOR(magnitude) ORDER BY FLOOR(magnitude)"
        ),
        "size": (12, 6),
    },
    {
        "name": "Seismes par jour",
        "display": "line",
        "sql": (
            "SELECT DATE_TRUNC('day', time)::date AS jour, "
            "COUNT(*) AS nb_seismes "
            "FROM earthquake GROUP BY jour ORDER BY jour"
        ),
        "size": (24, 6),
    },
    {
        "name": "Carte des seismes (M>=5)",
        "display": "map",
        "sql": (
            "SELECT id, place, magnitude, latitude, longitude "
            "FROM earthquake WHERE magnitude >= 5"
        ),
        "size": (12, 8),
        "viz_settings": {
            "map.type": "pin",
            "map.latitude_column": "latitude",
            "map.longitude_column": "longitude",
        },
    },
    {
        "name": "Carte des events EONET",
        "display": "map",
        "sql": (
            "SELECT e.id, e.title, "
            "(g.coordinates ->> 0)::numeric AS longitude, "
            "(g.coordinates ->> 1)::numeric AS latitude, g.date "
            "FROM event e JOIN geometry g ON g.event_id = e.id "
            "WHERE g.type = 'Point'"
        ),
        "size": (12, 8),
        "viz_settings": {
            "map.type": "pin",
            "map.latitude_column": "latitude",
            "map.longitude_column": "longitude",
        },
    },
    {
        "name": "Top rapprochements event <-> seisme",
        "display": "table",
        "sql": (
            "SELECT ev.title AS event_naturel, eq.place AS lieu_seisme, "
            "eq.magnitude, ee.distance_km, ee.delay_hours, eq.time AS date_seisme "
            "FROM event_earthquake ee "
            "JOIN event ev ON ev.id = ee.event_id "
            "JOIN earthquake eq ON eq.id = ee.earthquake_id "
            "ORDER BY ee.distance_km ASC"
        ),
        "size": (24, 8),
    },
    {
        "name": "Distribution distance / delai",
        "display": "scatter",
        "sql": (
            "SELECT ee.distance_km, ee.delay_hours, eq.magnitude "
            "FROM event_earthquake ee "
            "JOIN earthquake eq ON eq.id = ee.earthquake_id"
        ),
        "size": (12, 6),
    },
    {
        "name": "Seismes tsunami",
        "display": "table",
        "sql": (
            "SELECT place, magnitude, time, latitude, longitude "
            "FROM earthquake WHERE tsunami = true "
            "ORDER BY magnitude DESC"
        ),
        "size": (12, 6),
    },
]


def wait_for_metabase():
    for attempt in range(1, 61):
        try:
            response = requests.get(f"{METABASE_URL}/api/health", timeout=5)
            if response.status_code == 200:
                logger.info("Metabase up")
                return
        except requests.RequestException:
            pass
        logger.info("Attente Metabase (tentative %s/60)", attempt)
        time.sleep(5)
    raise RuntimeError("Metabase inaccessible")


def get_setup_token():
    response = requests.get(f"{METABASE_URL}/api/session/properties", timeout=10)
    response.raise_for_status()
    return response.json().get("setup-token")


def do_setup(setup_token):
    payload = {
        "token": setup_token,
        "user": {
            "first_name": ADMIN_FIRST,
            "last_name": ADMIN_LAST,
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "password_confirm": ADMIN_PASSWORD,
            "site_name": SITE_NAME,
        },
        "prefs": {
            "site_name": SITE_NAME,
            "site_locale": "fr",
            "allow_tracking": False,
        },
        "database": {
            "engine": "postgres",
            "name": "EONET / USGS",
            "details": {
                "host": POSTGRES_HOST,
                "port": POSTGRES_PORT,
                "dbname": POSTGRES_DB,
                "user": POSTGRES_USER,
                "password": POSTGRES_PASSWORD,
                "ssl": False,
                "tunnel-enabled": False,
                "advanced-options": False,
            },
            "is_full_sync": True,
        },
    }
    response = requests.post(f"{METABASE_URL}/api/setup", json=payload, timeout=60)
    if response.status_code >= 400:
        logger.error("Setup a echoue : %s %s", response.status_code, response.text)
    response.raise_for_status()
    return response.json()["id"]


def login():
    response = requests.post(
        f"{METABASE_URL}/api/session",
        json={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["id"]


def api(session_id):
    session = requests.Session()
    session.headers.update({"X-Metabase-Session": session_id, "Content-Type": "application/json"})
    return session


def find_postgres_db(session):
    response = session.get(f"{METABASE_URL}/api/database", timeout=15)
    response.raise_for_status()
    payload = response.json()
    databases = payload if isinstance(payload, list) else payload.get("data", [])
    for db in databases:
        if db.get("engine") == "postgres":
            return db["id"]
    raise RuntimeError("Base PostgreSQL introuvable dans Metabase")


def ensure_postgres_db(session):
    response = session.get(f"{METABASE_URL}/api/database", timeout=15)
    response.raise_for_status()
    payload = response.json()
    databases = payload if isinstance(payload, list) else payload.get("data", [])
    for db in databases:
        if db.get("engine") == "postgres":
            return db["id"]
    payload = {
        "engine": "postgres",
        "name": "EONET / USGS",
        "details": {
            "host": POSTGRES_HOST,
            "port": POSTGRES_PORT,
            "dbname": POSTGRES_DB,
            "user": POSTGRES_USER,
            "password": POSTGRES_PASSWORD,
            "ssl": False,
            "tunnel-enabled": False,
        },
    }
    response = session.post(f"{METABASE_URL}/api/database", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["id"]


def build_card_payload(card, database_id):
    query = {
        "type": "native",
        "native": {"query": card["sql"], "template-tags": {}},
        "database": database_id,
    }
    viz_settings = card.get("viz_settings", {})
    return {
        "name": card["name"],
        "display": card["display"],
        "dataset_query": query,
        "visualization_settings": viz_settings,
    }


def create_card(session, database_id, card):
    payload = build_card_payload(card, database_id)
    response = session.post(f"{METABASE_URL}/api/card", json=payload, timeout=60)
    if response.status_code >= 400:
        logger.error("Card '%s' KO : %s %s", card["name"], response.status_code, response.text)
        response.raise_for_status()
    return response.json()["id"]


def create_dashboard(session, name):
    payload = {"name": name, "collection_id": None}
    response = session.post(f"{METABASE_URL}/api/dashboard", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["id"]


def layout(cards):
    positions = []
    row = 0
    col = 0
    row_height = 0
    for index, card in enumerate(cards):
        width, height = card["size"]
        if col + width > 24:
            col = 0
            row += row_height
            row_height = 0
        positions.append({"row": row, "col": col, "size_x": width, "size_y": height})
        col += width
        row_height = max(row_height, height)
    return positions


def attach_cards(session, dashboard_id, card_ids, cards):
    positions = layout(cards)
    dashcards = []
    for index, card_id in enumerate(card_ids):
        pos = positions[index]
        dashcards.append(
            {
                "id": -(index + 1),
                "card_id": card_id,
                "col": pos["col"],
                "row": pos["row"],
                "size_x": pos["size_x"],
                "size_y": pos["size_y"],
                "parameter_mappings": [],
                "visualization_settings": {},
                "dashboard_tab_id": None,
                "series": [],
            }
        )
    payload = {"dashcards": dashcards}
    response = session.put(
        f"{METABASE_URL}/api/dashboard/{dashboard_id}",
        json=payload,
        timeout=30,
    )
    if response.status_code >= 400:
        logger.error("Ajout des cards KO : %s %s", response.status_code, response.text)
        response.raise_for_status()


def main():
    wait_for_metabase()
    setup_token = get_setup_token()

    if setup_token:
        logger.info("Setup initial de Metabase")
        session_id = do_setup(setup_token)
    else:
        logger.info("Metabase deja setup, connexion admin")
        session_id = login()

    session = api(session_id)
    database_id = ensure_postgres_db(session)
    logger.info("Base PostgreSQL id = %s", database_id)

    marker_url = f"{METABASE_URL}/api/dashboard"
    response = session.get(marker_url, timeout=15)
    response.raise_for_status()
    payload = response.json()
    dashboards = payload if isinstance(payload, list) else payload.get("data", [])
    for dashboard in dashboards:
        if dashboard.get("name") == "TP2 EONET vs USGS":
            logger.info("Dashboard deja present, rien a faire")
            return

    card_ids = []
    for card in CARDS:
        card_id = create_card(session, database_id, card)
        logger.info("Card creee : %s (id=%s)", card["name"], card_id)
        card_ids.append(card_id)

    dashboard_id = create_dashboard(session, "TP2 EONET vs USGS")
    logger.info("Dashboard cree : id=%s", dashboard_id)
    attach_cards(session, dashboard_id, card_ids, CARDS)
    logger.info("Dashboard alimente : %s cards", len(card_ids))


if __name__ == "__main__":
    main()
