# Minimal placeholders for typing compatibility
URLTypes = str
RequestContent = bytes | str | None
RequestFiles = dict[str, tuple[str, bytes, str]] | None
QueryParamTypes = dict[str, str] | None
HeaderTypes = dict[str, str] | list[tuple[str, str]] | None
CookieTypes = dict[str, str] | None
TimeoutTypes = float | None
AuthTypes = tuple[str, str] | None
