import os
import time

import requests
from requests.auth import HTTPBasicAuth

GEOSERVER_URL = os.getenv("GEOSERVER_URL", "http://geoserver:8080/geoserver")
GEOSERVER_USER = os.getenv("GEOSERVER_USER", "admin")
GEOSERVER_PASSWORD = os.getenv("GEOSERVER_PASSWORD", "geoserver")
GEOSERVER_WORKSPACE = os.getenv("GEOSERVER_WORKSPACE", "omi")
GEOSERVER_DATASTORE = os.getenv("GEOSERVER_DATASTORE", "omi_postgis")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "omi")
POSTGRES_USER = os.getenv("POSTGRES_USER", "omi")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "omi")

_auth = HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD)
_headers = {"Content-Type": "application/json"}


def _request(method: str, path: str, expected=(200, 201), payload=None):
    url = f"{GEOSERVER_URL}{path}"
    response = requests.request(
        method=method,
        url=url,
        auth=_auth,
        headers=_headers,
        json=payload,
        timeout=20,
    )
    if response.status_code in expected:
        return response
    if response.status_code == 401:
        raise RuntimeError("No autorizado para GeoServer. Revisa credenciales.")
    raise RuntimeError(f"GeoServer error {response.status_code}: {response.text}")


def wait_for_geoserver(max_retries: int = 30, sleep_seconds: int = 3):
    for _ in range(max_retries):
        try:
            response = requests.get(
                f"{GEOSERVER_URL}/rest/about/version.json",
                auth=_auth,
                timeout=10,
            )
            if response.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(sleep_seconds)
    raise RuntimeError("GeoServer no disponible tras múltiples reintentos")


def ensure_workspace():
    check = requests.get(
        f"{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}.json",
        auth=_auth,
        timeout=10,
    )
    if check.status_code == 200:
        return
    payload = {"workspace": {"name": GEOSERVER_WORKSPACE}}
    _request("POST", "/rest/workspaces", expected=(201,), payload=payload)


def ensure_datastore():
    check = requests.get(
        f"{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/datastores/{GEOSERVER_DATASTORE}.json",
        auth=_auth,
        timeout=10,
    )
    if check.status_code == 200:
        return

    payload = {
        "dataStore": {
            "name": GEOSERVER_DATASTORE,
            "connectionParameters": {
                "host": POSTGRES_HOST,
                "port": POSTGRES_PORT,
                "database": POSTGRES_DB,
                "schema": "public",
                "user": POSTGRES_USER,
                "passwd": POSTGRES_PASSWORD,
                "dbtype": "postgis",
                "Expose primary keys": True,
            },
        }
    }
    _request(
        "POST",
        f"/rest/workspaces/{GEOSERVER_WORKSPACE}/datastores",
        expected=(201,),
        payload=payload,
    )


def publish_featuretype(layer_name: str):
    check = requests.get(
        f"{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/datastores/{GEOSERVER_DATASTORE}/featuretypes/{layer_name}.json",
        auth=_auth,
        timeout=10,
    )
    if check.status_code == 200:
        return

    payload = {
        "featureType": {
            "name": layer_name,
            "nativeName": layer_name,
            "title": layer_name,
            "srs": "EPSG:4326",
            "enabled": True,
        }
    }
    _request(
        "POST",
        f"/rest/workspaces/{GEOSERVER_WORKSPACE}/datastores/{GEOSERVER_DATASTORE}/featuretypes",
        expected=(201,),
        payload=payload,
    )


def bootstrap_geoserver():
    wait_for_geoserver()
    ensure_workspace()
    ensure_datastore()
