import json
import urllib.parse
from typing import Any, Iterable, List, Tuple
from uuid import uuid4

from . import _types
from ._client import USE_CLIENT_DEFAULT


class Headers:
    def __init__(self, initial: dict[str, str] | Iterable[Tuple[str, str]] | None = None) -> None:
        self._items: List[Tuple[str, str]] = []
        if initial:
            if isinstance(initial, dict):
                self._items.extend([(k, v) for k, v in initial.items()])
            else:
                self._items.extend(list(initial))

    def multi_items(self) -> List[Tuple[str, str]]:
        return list(self._items)

    def __contains__(self, item: str) -> bool:
        item_lower = item.lower()
        return any(key.lower() == item_lower for key, _ in self._items)

    def get(self, key: str, default: str | None = None) -> str | None:
        for existing, value in self._items:
            if existing.lower() == key.lower():
                return value
        return default

    def __getitem__(self, item: str) -> str:
        result = self.get(item)
        if result is None:
            raise KeyError(item)
        return result

    def __iter__(self):
        return iter(dict(self._items))

    def items(self):
        return dict(self._items).items()

    def add(self, key: str, value: str) -> None:
        self._items.append((key, value))


class URL:
    def __init__(self, url: str) -> None:
        parsed = urllib.parse.urlsplit(url)
        self.scheme = parsed.scheme or "http"
        self.netloc = parsed.netloc.encode("ascii")
        self.path = parsed.path or "/"
        raw_path = self.path
        if parsed.query:
            raw_path = f"{self.path}?{parsed.query}"
        self.raw_path = raw_path.encode()
        self.query = parsed.query.encode()

    def join(self, url: str) -> "URL":
        return URL(urllib.parse.urljoin(self.as_str(), url))

    def as_str(self) -> str:
        query = f"?{self.query.decode()}" if self.query else ""
        return f"{self.scheme}://{self.netloc.decode()}{self.path}{query}"


class Request:
    def __init__(
        self,
        method: str,
        url: str,
        headers: Headers | None = None,
        content: bytes | str | None = None,
    ) -> None:
        self.method = method.upper()
        self.url = URL(url)
        self.headers = headers or Headers()
        if isinstance(content, str):
            content = content.encode()
        self._content = content or b""

    def read(self) -> bytes:
        return self._content


class ByteStream:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


class Response:
    def __init__(
        self,
        status_code: int,
        headers: Iterable[Tuple[str, str]] | dict[str, str],
        stream: ByteStream,
        request: Request,
    ) -> None:
        self.status_code = status_code
        if isinstance(headers, Headers):
            initial_headers = dict(headers.items())
        else:
            initial_headers = headers
        self.headers = Headers(initial_headers)
        self._stream = stream
        self.content = stream.read()
        self.request = request

    @property
    def text(self) -> str:
        return self.content.decode()

    def json(self) -> Any:
        return json.loads(self.content)


class BaseTransport:
    pass


class Client:
    def __init__(
        self,
        base_url: str | None = None,
        headers: dict[str, str] | None = None,
        transport: BaseTransport | None = None,
        follow_redirects: bool = False,
        cookies: dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url or ""
        self.headers = Headers(headers)
        self._transport = transport
        self.cookies = cookies or {}

    def _merge_url(self, url: str) -> str:
        if url.startswith("http://") or url.startswith("https://") or url.startswith("ws://") or url.startswith("wss://"):
            return url
        return urllib.parse.urljoin(self.base_url, url)

    def _encode_multipart(
        self, data: dict[str, str] | None, files: dict[str, tuple[str, bytes, str]] | None
    ) -> tuple[bytes, str]:
        boundary = uuid4().hex
        lines: list[bytes] = []
        for key, value in (data or {}).items():
            lines.append(f"--{boundary}".encode())
            disposition = f'Content-Disposition: form-data; name="{key}"'
            lines.append(disposition.encode())
            lines.append(b"")
            lines.append(value.encode())
        for key, file_tuple in (files or {}).items():
            filename, file_content, content_type = file_tuple
            lines.append(f"--{boundary}".encode())
            disposition = (
                f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'
            )
            lines.append(disposition.encode())
            lines.append(f"Content-Type: {content_type}".encode())
            lines.append(b"")
            lines.append(file_content)
        lines.append(f"--{boundary}--".encode())
        lines.append(b"")
        body = b"\r\n".join(lines)
        content_type = f"multipart/form-data; boundary={boundary}"
        return body, content_type

    def build_request(
        self,
        method: str,
        url: str,
        *,
        content: bytes | str | None = None,
        data: dict[str, str] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: Any = None,
        follow_redirects: Any = None,
        timeout: Any = None,
        extensions: dict[str, Any] | None = None,
    ) -> Request:
        merged_url = self._merge_url(url)
        if params:
            parsed = urllib.parse.urlsplit(merged_url)
            query_dict = dict(urllib.parse.parse_qsl(parsed.query))
            query_dict.update(params)
            query_string = urllib.parse.urlencode(query_dict)
            merged_url = urllib.parse.urlunsplit(
                (parsed.scheme, parsed.netloc, parsed.path, query_string, "")
            )

        request_headers = Headers(dict(self.headers.items()))
        if headers:
            for key, value in headers.items():
                request_headers.add(key, value)

        body: bytes | str | None = content
        if json is not None:
            body = json.dumps(json)
            request_headers.add("Content-Type", "application/json")
        elif files is not None or data is not None:
            body, content_type = self._encode_multipart(data, files)
            request_headers.add("Content-Type", content_type)

        return Request(method, merged_url, headers=request_headers, content=body)

    def request(self, method: str, url: str, **kwargs: Any) -> Response:
        request = self.build_request(method, url, **kwargs)
        if self._transport is None:
            raise RuntimeError("Transport is required for requests in this stub.")
        response = self._transport.handle_request(request)
        return response

    def get(self, url: str, **kwargs: Any) -> Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response:
        return self.request("POST", url, **kwargs)

    def options(self, url: str, **kwargs: Any) -> Response:
        return self.request("OPTIONS", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> Response:
        return self.request("HEAD", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> Response:
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Response:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Response:
        return self.request("DELETE", url, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class AsyncClient:  # pragma: no cover - not used in tests
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("AsyncClient is not implemented in this stub.")


__all__ = [
    "Client",
    "AsyncClient",
    "Request",
    "Response",
    "Headers",
    "BaseTransport",
    "ByteStream",
    "URL",
    "USE_CLIENT_DEFAULT",
    "_types",
]
