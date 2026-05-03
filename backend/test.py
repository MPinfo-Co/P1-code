from app.utils.util_store import create_access_token

t = create_access_token({"sub": "1"})
print(t)