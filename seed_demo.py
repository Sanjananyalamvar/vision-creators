"""Creates the demo user from the login wireframe plus sample memories. Usage: python seed_demo.py [base_url]"""
import sys, httpx
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000") + "/api/v1"
U = {"full_name": "Alex Vance", "email": "alex@company.com", "password": "RecallMemoryPass2025"}
c = httpx.Client(timeout=20)
r = c.post(f"{BASE}/auth/signup", json=U)
if r.status_code == 409:
    r = c.post(f"{BASE}/auth/login", json={"identifier": U["email"], "password": U["password"]})
h = {"Authorization": "Bearer " + r.json()["access_token"]}
CARDS = [
 ("What is the CAP Theorem, and how does Apache Cassandra handle network partitions?",
  "CAP: a distributed store can't guarantee Consistency, Availability and Partition tolerance together. Cassandra is AP: it stays available and offers tunable consistency (W + R > N).",
  "Think tunable consistency and quorum calculations.", ["distributed-systems"]),
 ("Why choose pgvector over a dedicated vector DB?", "Keeps embeddings next to relational data, one system to operate, good enough up to a few million vectors.", None, ["engineering", "vector-db"]),
 ("Alex's dietary preferences?", "Prefers oat milk lattes, allergic to shellfish. Flying SFO to NYC on Thursday.", None, ["personal", "preferences"]),
]
for q, a, hint, tags in CARDS:
    c.post(f"{BASE}/memories", headers=h, json={"content": a, "title": q[:60], "question": q, "answer": a, "hint": hint, "tags": tags, "partition": "work"})
print("seeded; login as", U["email"], "/", U["password"])
