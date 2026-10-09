def test_unauthenticated_access_redirects(client):
    res = client.get("/kanban", follow_redirects=False)
    assert res.status_code in [302, 401]
    assert "/auth/login" in res.headers.get("Location", "")


def test_regular_user_cannot_access_staff_routes(client, db):
    # Log in as regular user
    client.post("/auth/login", data={"email": "user@example.com", "password": "Password123!"})
    
    # Try staff route
    res = client.get("/kanban")
    assert res.status_code == 403

    # Try admin route
    res = client.get("/admin/settings")
    assert res.status_code == 403


def test_staff_can_access_kanban_but_not_admin(client, db):
    # Log in as staff
    client.post("/auth/login", data={"email": "staff@example.com", "password": "Password123!"})
    
    # Kanban accessible
    res = client.get("/kanban")
    assert res.status_code == 200

    # Admin settings blocked with 403
    res = client.get("/admin/settings")
    assert res.status_code == 403


def test_admin_can_access_admin_settings(client, db):
    # Log in as admin
    client.post("/auth/login", data={"email": "admin@example.com", "password": "Password123!"})
    
    res = client.get("/admin/settings")
    assert res.status_code == 200
