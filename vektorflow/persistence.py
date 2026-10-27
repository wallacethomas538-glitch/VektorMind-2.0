"""Mission persistence for the Hackathon 2026 Supabase project only.

This module deliberately reads *only* ``HACKATHON_SUPABASE_URL`` and
``HACKATHON_SUPABASE_KEY``. The generic ``SUPABASE_URL`` / ``SUPABASE_KEY``
variables belong to the frozen VektorFlow-15xr system and are never touched.

Writes use the Supabase REST API (PostgREST) against three tables:
``missions``, ``mission_receipts``, and ``approvals``. RLS is expected to be
on. Use a service-role key on the server, or add tightly scoped policies.

No secret is ever returned in a status report or an error.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

ENV_URL = "HACKATHON_SUPABASE_URL"
ENV_KEY = "HACKATHON_SUPABASE_KEY"
ENV_TIMEOUT = "HACKATHON_SUPABASE_TIMEOUT"

PROJECT_LABEL = "hackathon-2026"
TABLES = ("missions", "mission_receipts", "approvals")


class PersistenceError(RuntimeError):
    """A sanitized persistence failure. The report never contains secrets."""

    def __init__(self, message: str, report: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.report = report or {
            "backend": "supabase",
            "project": PROJECT_LABEL,
            "stored": False,
            "status": "error",
        }


@dataclass(frozen=True)
class StoreConfig:
    url: str
    key: str
    timeout: float


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _timeout() -> float:
    raw = os.getenv(ENV_TIMEOUT, "5").strip()
    try:
        value = float(raw)
    except ValueError:
        return 5.0
    return max(1.0, min(15.0, value))


def configuration_status() -> Dict[str, Any]:
    """Return a secret-free description of the configured persistence target."""

    url = (os.getenv(ENV_URL) or "").strip()
    key = (os.getenv(ENV_KEY) or "").strip()
    base = {
        "backend": "in-memory",
        "project": PROJECT_LABEL,
        "env": [ENV_URL, ENV_KEY],
        "tables": list(TABLES),
        "reads_generic_supabase_env": False,
    }
    if not url and not key:
        base.update({"state": "unconfigured", "configured": False})
        return base
    if not url or not key:
        base.update({"state": "incomplete", "configured": False})
        return base
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".supabase.co"):
        base.update({"state": "invalid_url", "configured": False})
        return base
    base.update({"state": "ready", "configured": True, "backend": "supabase"})
    return base


def persistence_target() -> str:
    return "supabase_hackathon_2026" if configuration_status()["state"] == "ready" else "in-memory"


def _config() -> tuple[Optional[StoreConfig], Dict[str, Any]]:
    status = configuration_status()
    if status["state"] != "ready":
        return None, status
    return (
        StoreConfig(
            url=(os.getenv(ENV_URL) or "").strip().rstrip("/"),
            key=(os.getenv(ENV_KEY) or "").strip(),
            timeout=_timeout(),
        ),
        status,
    )


def _headers(cfg: StoreConfig) -> Dict[str, str]:
    return {
        "apikey": cfg.key,
        "Authorization": f"Bearer {cfg.key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _endpoint(cfg: StoreConfig, table: str) -> str:
    return f"{cfg.url}/rest/v1/{table}"


def _report(config_status: Dict[str, Any], **extra: Any) -> Dict[str, Any]:
    report = {
        "backend": "supabase" if config_status.get("state") == "ready" else "in-memory",
        "project": PROJECT_LABEL,
        "tables": list(TABLES),
        "stored": False,
        "status": config_status.get("state", "unknown"),
    }
    report.update(extra)
    return report


def _failure(table: str, exc: Exception) -> PersistenceError:
    http_status = getattr(getattr(exc, "response", None), "status_code", None)
    return PersistenceError(
        f"supabase_{table}_failed",
        report={
            "backend": "supabase",
            "project": PROJECT_LABEL,
            "tables": list(TABLES),
            "stored": False,
            "status": "error",
            "failed_table": table,
            "error": type(exc).__name__,
            "http_status": http_status,
        },
    )


def _upsert(
    client: httpx.Client,
    cfg: StoreConfig,
    table: str,
    row: Dict[str, Any],
    conflict: str,
) -> None:
    response = client.post(
        _endpoint(cfg, table),
        params={"on_conflict": conflict},
        headers={
            **_headers(cfg),
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
        json=row,
    )
    response.raise_for_status()


def save_mission(receipt: Dict[str, Any], client: Optional[httpx.Client] = None) -> Dict[str, Any]:
    """Upsert a staged mission, its receipt, and its pending approvals.

    Returns a sanitized report. A configured-but-unreachable project raises
    :class:`PersistenceError`; the caller decides whether to surface it.
    """

    cfg, status = _config()
    if cfg is None:
        return _report(
            status,
            note="Hackathon 2026 Supabase is not configured; receipt kept in memory only.",
        )

    mission_id = str(receipt.get("mission_id") or "")
    if not mission_id:
        raise PersistenceError("missing_mission_id", report=_report(status, status="error"))

    issued_at = str(receipt.get("receipt", {}).get("issued_at") or _now())
    updated_at = _now()

    mission_row = {
        "id": mission_id,
        "objective": receipt.get("objective") or {},
        "status": receipt.get("status") or "staged_for_approval",
        "plan": receipt.get("plan") or [],
        "risk": receipt.get("risk") or {},
        "kill_switch": bool(receipt.get("kill_switch", False)),
        "meta_served": bool(receipt.get("meta_served", False)),
        "image_served": bool(receipt.get("image_served", False)),
        "created_at": issued_at,
        "updated_at": updated_at,
    }
    receipt_row = {
        "mission_id": mission_id,
        "receipt": receipt,
        "status": receipt.get("status") or "staged_for_approval",
        "meta_served": bool(receipt.get("meta_served", False)),
        "image_served": bool(receipt.get("image_served", False)),
        "created_at": issued_at,
        "updated_at": updated_at,
    }

    owns_client = client is None
    if client is None:
        client = httpx.Client(timeout=cfg.timeout)

    steps: List[Dict[str, Any]] = []
    try:
        _upsert(client, cfg, "missions", mission_row, "id")
        steps.append({"table": "missions", "status": "stored"})

        _upsert(client, cfg, "mission_receipts", receipt_row, "mission_id")
        steps.append({"table": "mission_receipts", "status": "stored"})

        for approval in receipt.get("approvals") or []:
            approval_row = {
                "mission_id": mission_id,
                "approver": approval.get("approver") or "Wallace",
                "role": approval.get("role") or "final tap",
                "status": approval.get("status") or "pending",
                "scope": approval.get("scope") or "",
                "requested_at": approval.get("requested_at") or issued_at,
                "decided_at": approval.get("decided_at"),
            }
            _upsert(client, cfg, "approvals", approval_row, "mission_id,approver")
        steps.append({"table": "approvals", "status": "stored", "rows": len(receipt.get("approvals") or [])})
    except (httpx.HTTPError, httpx.InvalidURL) as exc:
        raise _failure(steps[-1]["table"] if steps else "missions", exc) from None
    finally:
        if owns_client:
            client.close()

    return _report(status, stored=True, status="stored", steps=steps)


def fetch_receipt(mission_id: str, client: Optional[httpx.Client] = None) -> Optional[Dict[str, Any]]:
    """Load a receipt from the Hackathon 2026 project.

    Returns ``None`` only when the mission does not exist there. A missing
    receipt for an existing mission is a storage error, not a 404.
    """

    cfg, status = _config()
    if cfg is None:
        if status["state"] == "unconfigured":
            return None
        raise PersistenceError(
            f"supabase_config_{status['state']}",
            report=_report(status, status=status["state"]),
        )

    owns_client = client is None
    if client is None:
        client = httpx.Client(timeout=cfg.timeout)

    try:
        response = client.get(
            _endpoint(cfg, "mission_receipts"),
            params={"mission_id": f"eq.{mission_id}", "select": "receipt"},
            headers=_headers(cfg),
        )
        response.raise_for_status()
        rows = response.json()
        if not isinstance(rows, list):
            raise PersistenceError(
                "supabase_mission_receipts_invalid_response",
                report=_report(status, status="error", failed_table="mission_receipts"),
            )
        if rows:
            receipt = rows[0].get("receipt") if isinstance(rows[0], dict) else None
            if isinstance(receipt, dict):
                return receipt
            raise PersistenceError(
                "supabase_mission_receipts_invalid_row",
                report=_report(status, status="error", failed_table="mission_receipts"),
            )

        mission_response = client.get(
            _endpoint(cfg, "missions"),
            params={"id": f"eq.{mission_id}", "select": "id"},
            headers=_headers(cfg),
        )
        mission_response.raise_for_status()
        missions = mission_response.json()
        if isinstance(missions, list) and missions:
            raise PersistenceError(
                "supabase_receipt_missing_for_existing_mission",
                report=_report(status, status="error", failed_table="mission_receipts"),
            )
        return None
    except (httpx.HTTPError, httpx.InvalidURL) as exc:
        raise _failure("mission_receipts", exc) from None
    finally:
        if owns_client:
            client.close()
