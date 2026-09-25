import logging
import os
import sys
import time

import docker
from prometheus_client import start_http_server, Gauge

REFRESH_SECONDS = int(os.environ.get("EXPORTER_REFRESH_SECONDS", "20"))
EXPORTER_PORT = int(os.environ.get("EXPORTER_PORT", "9106"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("docker-stats-exporter")

cpu_percent = Gauge("container_cpu_percent", "Pourcentage CPU du conteneur", ["name"])
mem_usage_bytes = Gauge("container_mem_usage_bytes", "Memoire utilisee par le conteneur", ["name"])
mem_limit_bytes = Gauge("container_mem_limit_bytes", "Limite memoire du conteneur", ["name"])
container_up = Gauge("container_state_running", "1 si le conteneur tourne", ["name"])


def compute_cpu_percent(stats):
    cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    system_delta = stats["cpu_stats"].get("system_cpu_usage", 0) - stats["precpu_stats"].get("system_cpu_usage", 0)
    online_cpus = stats["cpu_stats"].get("online_cpus") or len(stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [1]))
    if system_delta > 0 and cpu_delta > 0:
        return (cpu_delta / system_delta) * online_cpus * 100.0
    return 0.0


def refresh(client):
    for container in client.containers.list():
        try:
            stats = container.stats(stream=False)
            cpu_percent.labels(name=container.name).set(compute_cpu_percent(stats))
            mem_usage_bytes.labels(name=container.name).set(stats["memory_stats"].get("usage", 0))
            mem_limit_bytes.labels(name=container.name).set(stats["memory_stats"].get("limit", 0))
            container_up.labels(name=container.name).set(1)
        except Exception:
            logger.exception("Echec stats pour %s", container.name)


def main():
    start_http_server(EXPORTER_PORT)
    client = docker.from_env()
    logger.info("Exporter demarre sur le port %s", EXPORTER_PORT)
    while True:
        try:
            refresh(client)
        except Exception:
            logger.exception("Echec du refresh")
        time.sleep(REFRESH_SECONDS)


if __name__ == "__main__":
    main()
