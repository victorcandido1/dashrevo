"""Test script to verify endpoints are working"""
import sys
sys.path.insert(0, '.')

from flask import Flask
from routes.api import api_bp

app = Flask(__name__)
app.register_blueprint(api_bp, url_prefix='/api')

# List all routes
print("="*60)
print("Registered Routes:")
print("="*60)
for rule in app.url_map.iter_rules():
    if 'kpis' in rule.rule:
        print(f"  {rule.rule} -> {rule.endpoint}")

print("\n" + "="*60)
print("Testing endpoints:")
print("="*60)

with app.test_client() as client:
    # Test commercial-hours
    r = client.get('/api/kpis/commercial-hours')
    print(f"\n1. /api/kpis/commercial-hours")
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        import json
        data = json.loads(r.get_data(as_text=True))
        print(f"   Response: {json.dumps(data, indent=2)[:200]}")
    else:
        print(f"   Response: {r.get_data(as_text=True)[:200]}")
    
    # Test accumulated
    r = client.get('/api/kpis/accumulated')
    print(f"\n2. /api/kpis/accumulated")
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        import json
        data = json.loads(r.get_data(as_text=True))
        print(f"   Response: {json.dumps(data, indent=2)[:200]}")
    else:
        print(f"   Response: {r.get_data(as_text=True)[:200]}")

