#!/usr/bin/env python3
"""
Test server connection and endpoints
"""
import asyncio
import httpx

async def test_server():
    """Test if server is running and endpoints are accessible"""
    async with httpx.AsyncClient() as client:
        try:
            # Test docs endpoint
            response = await client.get("http://localhost:8000/docs")
            print(f"Docs endpoint status: {response.status_code}")
            
            # Test auth endpoints
            response = await client.get("http://localhost:8000/auth/")
            print(f"Auth endpoint status: {response.status_code}")
            
            # Test forgot password endpoint
            response = await client.post("http://localhost:8000/auth/forgot-password", json={"email_or_username": "test@example.com"})
            print(f"Forgot password endpoint status: {response.status_code}")
            print(f"Response: {response.text}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_server())
