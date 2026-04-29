from app.core.security import create_access_token

t = create_access_token({"sub": "1"})
print(t)