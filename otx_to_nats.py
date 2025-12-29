# otx_to_nats.py
from OTXv2 import OTXv2
import asyncio
from nats.aio.client import Client as NATS
import json
from datetime import datetime, timedelta

class OTX_to_NATS:
    def __init__(self, otx_key, nats_url):
        self.otx = OTXv2(otx_key)
        self.nats_url = nats_url
    
    async def fetch_pulses(self, days=1):
        nc = NATS()
        await nc.connect(self.nats_url)
        js = nc.jetstream()
        
        # Получаем последние pulses
        modified_since = (datetime.now() - timedelta(days=days)).isoformat()
        pulses = self.otx.getall(modified_since=modified_since)
        
        for pulse in pulses:
            for indicator in pulse['indicators']:
                ioc = {
                    "value": indicator['indicator'],
                    "type": self._normalize_type(indicator['type']),
                    "threat_type": pulse['name'],
                    "source": "AlienVault OTX",
                    "confidence": 75,
                    "timestamp": pulse['modified'],
                    "pulse_id": pulse['id'],
                    "tags": pulse['tags'],
                    "description": pulse['description']
                }
                
                subject = f"ioc.{ioc['type']}"
                await js.publish(subject, json.dumps(ioc).encode())
        
        await nc.close()
    
    def _normalize_type(self, otx_type):
        type_mapping = {
            'IPv4': 'ip',
            'IPv6': 'ip',
            'domain': 'domain',
            'hostname': 'domain',
            'FileHash-MD5': 'hash',
            'FileHash-SHA1': 'hash',
            'FileHash-SHA256': 'hash',
            'URL': 'url',
            'email': 'email'
        }
        return type_mapping.get(otx_type, 'other')

# Запуск каждый час
async def main():
    collector = OTX_to_NATS(
        otx_key="YOUR_OTX_KEY",
        nats_url="nats://localhost:4222"
    )
    
    while True:
        await collector.fetch_pulses(days=1)
        print("Waiting 1 hour...")
        await asyncio.sleep(3600)

asyncio.run(main())
