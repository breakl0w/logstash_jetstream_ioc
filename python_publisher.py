# publish_ioc.py
import asyncio
import json
from nats.aio.client import Client as NATS

async def publish_ioc():
    nc = NATS()
    await nc.connect("nats://localhost:4222")
    js = nc.jetstream()
    
    # Тестовые IoC
    iocs = [
        {
            "value": "192.168.1.100",
            "type": "ip",
            "threat_type": "malware",
            "source": "test_feed",
            "confidence": 85,
            "timestamp": "2024-01-15T10:00:00Z"
        },
        {
            "value": "evil.com",
            "type": "domain",
            "threat_type": "phishing",
            "source": "test_feed",
            "confidence": 90,
            "timestamp": "2024-01-15T10:01:00Z"
        },
        {
            "value": "5d41402abc4b2a76b9719d911017c592",
            "type": "hash",
            "threat_type": "ransomware",
            "source": "test_feed",
            "confidence": 95,
            "timestamp": "2024-01-15T10:02:00Z"
        }
    ]
    
    for ioc in iocs:
        subject = f"ioc.{ioc['type']}"
        message = json.dumps(ioc)
        
        ack = await js.publish(subject, message.encode())
        print(f"✓ Published {ioc['value']} to {subject}, seq: {ack.seq}")
    
    await nc.close()

if __name__ == "__main__":
    asyncio.run(publish_ioc())
