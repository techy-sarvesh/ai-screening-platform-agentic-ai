import uuid

def generate_assessment_token() -> str:
    return uuid.uuid4().hex

def generate_assessment_url(base_url: str, token: str) -> str:
    # Ensure there are no double slashes except after http(s):
    base_url = base_url.rstrip("/")
    return f"{base_url}/test/{token}"
