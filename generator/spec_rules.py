"""Allow-lists copied from the v1.5 screen models. Anything else is an error."""

SUPPORTED_OPERATIONS = frozenset(
    {
        "APPLY_DEFAULTS",
        "CALL_API",
        "CALL_EVENT",
        "VALIDATE",
        "RESET_PAGE",
        "APPLY_QUERY",
        "NAVIGATE",
        "READ_ROUTE",
        "MARK_PRISTINE",
    }
)
SUPPORTED_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
SUPPORTED_LOCATIONS = frozenset({"QUERY", "BODY", "PATH"})
SUPPORTED_MAPPINGS = frozenset({"SET", "REPLACE"})
SUPPORTED_AREAS = frozenset({"QUERY", "ACTIONS", "LIST", "FORM", "DETAIL"})
BODY_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
