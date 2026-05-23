import asyncio
import os

import httpx


async def test_security():
    base_url = "http://127.0.0.1:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        print("\n--- 1. Testing Unauthenticated Access ---")
        res = await client.post(f"{base_url}/query", json={"query": "Hello", "session_id": "test_123"})
        print(f"Status: {res.status_code} (Expected 401 Unauthorized)")
        
        print("\n--- 2. Logging in as Standard User (Aryan) ---")
        login_res = await client.post(f"{base_url}/auth/login", data={"username": "aryan", "password": os.getenv("TEST_USER_PASSWORD", "dummy_pass")})
        aryan_token = login_res.json().get("access_token")
        print(f"Obtained JWT Token: {aryan_token[:20]}...")
        
        print("\n--- 3. Testing RBAC: Aryan trying to Ingest a file (Admin Only) ---")
        headers = {"Authorization": f"Bearer {aryan_token}"}
        files = {'file': ('test.txt', b'This is a test document.')}
        res = await client.post(f"{base_url}/ingest", headers=headers, files=files)
        print(f"Status: {res.status_code} (Expected 403 Forbidden)")
        
        print("\n--- 4. Logging in as Admin ---")
        login_res = await client.post(f"{base_url}/auth/login", data={"username": "admin", "password": os.getenv("TEST_ADMIN_PASSWORD", "dummy_admin_pass")})
        admin_token = login_res.json().get("access_token")
        
        print("\n--- 5. Testing RBAC: Admin trying to Ingest a file ---")
        headers = {"Authorization": f"Bearer {admin_token}"}
        files = {'file': ('test.txt', b'This is a test document.')}
        res = await client.post(f"{base_url}/ingest", headers=headers, files=files)
        print(f"Status: {res.status_code} (Expected 200 OK)")

if __name__ == "__main__":
    asyncio.run(test_security())