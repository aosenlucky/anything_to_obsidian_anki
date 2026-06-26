from __future__ import annotations

import os
import json
import subprocess
from dataclasses import dataclass
from typing import Any

import requests

from app.config import AppConfig


class CloudInboxError(RuntimeError):
    pass


@dataclass
class CloudInboxItem:
    id: str
    source_type: str
    raw_input: str
    title: str | None = None
    my_intent: str | None = None
    domain_hint: str | None = None
    source_url: str | None = None


class CloudInboxClient:
    def __init__(self, config: AppConfig):
        inbox_config = config.section("cloud_inbox")
        self.api_url = str(inbox_config.get("api_url", "")).rstrip("/")
        token_env = inbox_config.get("agent_token_env", "CLOUD_INBOX_AGENT_TOKEN")
        self.token = os.getenv(token_env)
        if not self.api_url or self.api_url == "https://your-inbox.vercel.app":
            raise CloudInboxError("cloud_inbox.api_url 未配置，请先在 config.yaml 中填写 Vercel Inbox 地址。")
        if not self.token:
            raise CloudInboxError(f"未找到环境变量 {token_env}，请先配置 Cloud Inbox Agent Token。")

    def list_queued(self, limit: int = 10) -> list[CloudInboxItem]:
        response = self._request("GET", f"/api/agent/items?limit={limit}")
        items = response.get("items", [])
        return [CloudInboxItem(**_normalize_item(item)) for item in items]

    def update_item(
        self,
        item_id: str,
        status: str,
        source_path: str | None = None,
        note_paths: list[str] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": status}
        if source_path:
            payload["source_path"] = source_path
        if note_paths is not None:
            payload["note_paths"] = note_paths
        if error:
            payload["error"] = error
        return self._request("PATCH", f"/api/agent/items/{item_id}", json=payload)

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        try:
            response = requests.request(
                method,
                f"{self.api_url}{path}",
                headers=headers,
                timeout=20,
                **kwargs,
            )
        except requests.RequestException as exc:
            return self._request_with_powershell(method, path, headers=headers, **kwargs)
        try:
            data = response.json()
        except ValueError as exc:
            raise CloudInboxError(f"Cloud Inbox 返回了非 JSON 响应：HTTP {response.status_code}") from exc
        if response.status_code >= 400:
            raise CloudInboxError(data.get("error") or f"Cloud Inbox HTTP {response.status_code}")
        return data

    def _request_with_powershell(self, method: str, path: str, headers: dict[str, str], **kwargs: Any) -> dict[str, Any]:
        body = kwargs.get("json")
        command = r"""
$ErrorActionPreference='Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Net.Http
$client = [System.Net.Http.HttpClient]::new()
$client.Timeout = [TimeSpan]::FromSeconds(60)
$headers = ConvertFrom-Json $env:LAP_HEADERS_JSON
foreach ($property in $headers.PSObject.Properties) {
  if ($property.Name -eq 'Authorization') {
    $client.DefaultRequestHeaders.Authorization = [System.Net.Http.Headers.AuthenticationHeaderValue]::Parse($property.Value)
  } else {
    [void]$client.DefaultRequestHeaders.TryAddWithoutValidation($property.Name, $property.Value)
  }
}
$method = [System.Net.Http.HttpMethod]::new($env:LAP_METHOD)
$request = [System.Net.Http.HttpRequestMessage]::new($method, $env:LAP_URL)
if ($env:LAP_BODY_JSON) {
  $request.Content = [System.Net.Http.StringContent]::new($env:LAP_BODY_JSON, [System.Text.Encoding]::UTF8, 'application/json')
}
$response = $client.SendAsync($request).GetAwaiter().GetResult()
$text = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
if (-not $response.IsSuccessStatusCode) {
  throw "HTTP $([int]$response.StatusCode): $text"
}
$text
"""
        env = os.environ.copy()
        env["LAP_METHOD"] = method
        env["LAP_URL"] = f"{self.api_url}{path}"
        env["LAP_HEADERS_JSON"] = json.dumps(headers, ensure_ascii=False)
        env["LAP_BODY_JSON"] = json.dumps(body, ensure_ascii=False) if body is not None else ""
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=75,
            env=env,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            raise CloudInboxError(f"Cloud Inbox 请求失败：{detail}")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise CloudInboxError("Cloud Inbox PowerShell 备用请求返回了非 JSON 响应。") from exc


def _normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "source_type": item.get("source_type") or "manual",
        "raw_input": item.get("raw_input") or "",
        "title": item.get("title"),
        "my_intent": item.get("my_intent"),
        "domain_hint": item.get("domain_hint"),
        "source_url": item.get("source_url"),
    }
