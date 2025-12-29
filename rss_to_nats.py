# rss_to_nats.py
import feedparser
import asyncio
from nats.aio.client import Client as NATS
import json
import re
from datetime import datetime

class RSSFeedCollector:
    def __init__(self, nats_url):
        self.nats_url = nats_url
        self.feeds = [
            "https://www.cisa.gov/cybersecurity-advisories/all.xml",
            "https://www.us-cert.gov/ncas/current-activity.xml",
            # Добавь свои фиды
        ]
    
    async def collect(self):
        nc = NATS()
        await nc.connect(self.nats_url)
        js = nc.jetstream()
        
        for feed_url in self.feeds:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries:
                # Извлекаем IoC из описания
                iocs = self._extract_iocs(entry.description)
                
                for ioc in iocs:
                    ioc['source'] = feed.feed.title
                    ioc['timestamp'] = datetime.now().isoformat()
                    ioc['reference_url'] = entry.link
                    
                    subject = f"ioc.{ioc['type']}"
                    await js.publish(subject, json.dumps(ioc).encode())
        
        await nc.close()
    
    def _extract_iocs(self, text):
        iocs = []
        
        # IP адреса
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        for ip in re.findall(ip_pattern, text):
            iocs.append({
                "value": ip,
                "type": "ip",
                "threat_type": "unknown",
                "confidence": 60
            })
        
        # Домены
        domain_pattern = r'\b[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(?:\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+\b'
        for domain in re.findall(domain_pattern, text):
            if not domain.endswith(('.png', '.jpg', '.gif')):
                iocs.append({
                    "value": domain,
                    "type": "domain",
                    "threat_type": "unknown",
                    "confidence": 60
                })
        
        # SHA256 хеши
        hash_pattern = r'\b[a-fA-F0-9]{64}\b'
        for hash_val in re.findall(hash_pattern, text):
            iocs.append({
                "value": hash_val,
                "type": "hash",
                "threat_type": "unknown",
                "confidence": 70
            })
        
        return iocs

# Запуск каждые 30 минут
async def main():
    collector = RSSFeedCollector("nats://localhost:4222")
    
    while True:
        await collector.collect()
        print("Collected from RSS feeds, waiting 30 minutes...")
        await asyncio.sleep(1800)

asyncio.run(main())
