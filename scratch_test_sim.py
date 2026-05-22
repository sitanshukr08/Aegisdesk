import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

INTENT_CLASSES = [
    {"category": "greeting", "domain": None, "keywords": "hi hello thanks hey greetings good morning afternoon"},
    {"category": "it_support", "domain": "network_diagnostics", "keywords": "ping ipconfig network internet slow wifi connection vpn disconnected ethernet latency routing broken pipe"},
    {"category": "it_support", "domain": "cloud_integrations", "keywords": "okta jira slack reset password unlock account ticket aws azure active directory sso login token expired"},
    {"category": "it_support", "domain": "web_scraping", "keywords": "scrape read wiki documentation hr portal benefits policy external website url page"},
]

model = SentenceTransformer('all-MiniLM-L6-v2')
corpus = [item["keywords"] for item in INTENT_CLASSES]
intent_vectors = model.encode(corpus, convert_to_numpy=True)

queries = [
    "I can't reach the corporate gateway",
    "My Okta session died"
]

for q in queries:
    q_vec = model.encode([q], convert_to_numpy=True)
    sim = cosine_similarity(q_vec, intent_vectors).flatten()
    best_idx = int(np.argmax(sim))
    print(f"Query: {q}")
    print(f"Similarities: {sim}")
    print(f"Best match: {INTENT_CLASSES[best_idx]['domain']} with score {sim[best_idx]}")
