from multimodal_suite import db
import json
import sqlite3

u = db.create_user("studio.verify@example.com", "CorrectHorse1", "Studio Tester")
assert u.email == "studio.verify@example.com"
assert db.authenticate_user("studio.verify@example.com", "wrong") is None
assert db.authenticate_user("studio.verify@example.com", "CorrectHorse1").id == u.id
try:
    db.create_user("studio.verify@example.com", "CorrectHorse1")
    raise SystemExit("duplicate should fail")
except ValueError as exc:
    assert "already exists" in str(exc)

conn = sqlite3.connect(db.DB_PATH)
row = conn.execute("SELECT password_hash FROM users WHERE email=?", (u.email,)).fetchone()
assert "CorrectHorse1" not in row[0]
assert row[0].startswith("pbkdf2_sha256$")
token = db.create_remember_token(u.id)
assert db.user_from_remember_token(token).email == u.email
db.revoke_remember_token(token)
assert db.user_from_remember_token(token) is None

c = db.save_campaign("Auth UI Check", "desc", {"headline": "Keep Gemini", "tagline": "ok"})
got = db.get_campaign_by_id(c.id)
payload = json.loads(got.brief)
assert payload["headline"] == "Keep Gemini"
conn.execute("DELETE FROM campaigns WHERE id=?", (c.id,))
conn.execute("DELETE FROM remember_tokens WHERE user_id=?", (u.id,))
conn.execute("DELETE FROM users WHERE email=?", (u.email,))
conn.commit()
conn.close()
print("auth+save checks passed")
print("email_err", db.validate_email("bad"))
print("pw_err", db.validate_password("short"))
print("mismatch", db.validate_password("longenough", "otherpass"))
