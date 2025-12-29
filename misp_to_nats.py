# misp_to_nats.py
import asyncio
from pymisp import PyMISP
from nats.aio.client import Client as NATS
import json

class MISP_to_NATS:
    def __init__(self, misp_url, misp_key, nats_url):
        self.misp = PyMISP(misp_url, misp_key, False)
        self.nats_url = nats_url
        
    async def fetch_and_publish(self):
        nc = NATS()
        await nc.connect(self.nats_url)
        js = nc.jetstream()
        
        # Получаем события за последние 24 часа
        events = self.misp.search(
            controller='events',
            published=True,
            timestamp='1d'
        )
        
        for event in events:
            for attribute in event['Event']['Attribute']:
                ioc = {
                    "value": attribute['value'],
                    "type": attribute['type'],
                    "category": attribute['category'],
                    "threat_type": event['Event']['info'],
                    "source": "MISP",
                    "confidence": self._calculate_confidence(attribute),
                    "timestamp": attribute['timestamp'],
                    "event_id": event['Event']['id'],
                    "tags": [tag['name'] for tag in attribute.get('Tag', [])]
                }
                
                subject = f"ioc.{self._normalize_type(attribute['type'])}"
                await js.publish(subject, json.dumps(ioc).encode())
                print(f"Published IoC: {ioc['value']}")
        
        await nc.close()
    
    def _normalize_type(self, misp_type):
        type_mapping = {
            'ip-src': 'ip',
            'ip-dst': 'ip',
            'domain': 'domain',
            'hostname': 'domain',
            'md5': 'hash',
            'sha1': 'hash',
            'sha256': 'hash',
            'url': 'url',
            'email-src': 'email'
        }
        return type_mapping.get(misp_type, 'other')
    
    def _calculate_confidence(self, attribute):
        # Логика расчета confidence на основе MISP данных
        base_confidence = 50
        if attribute.get('to_ids'):
            base_confidence += 20
        if len(attribute.get('Tag', [])) > 0:
            base_confidence += 10
        return min(base_confidence, 100)

# Запуск
async def main():
    collector = MISP_to_NATS(
        misp_url="https://misp.example.com",
        misp_key="YOUR_API_KEY",
        nats_url="nats://localhost:4222"
    )
    await collector.fetch_and_publish()

asyncio.run(main())
