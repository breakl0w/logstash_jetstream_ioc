# api_to_nats.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from nats.aio.client import Client as NATS
import json
from typing import List, Optional

app = FastAPI()

class IoC(BaseModel):
    value: str
    type: str  # ip, domain, hash, url, email
    threat_type: str
    source: str
    confidence: int
    tags: Optional[List[str]] = []
    description: Optional[str] = None

class NATSPublisher:
    def __init__(self):
        self.nc = None
        self.js = None
    
    async def connect(self):
        self.nc = NATS()
        await self.nc.connect("nats://localhost:4222")
        self.js = self.nc.jetstream()
    
    async def publish(self, ioc: IoC):
        subject = f"ioc.{ioc.type}"
        message = ioc.dict()
        await self.js.publish(subject, json.dumps(message).encode())

publisher = NATSPublisher()

@app.on_event("startup")
async def startup():
    await publisher.connect()

@app.post("/api/v1/ioc")
async def submit_ioc(ioc: IoC):
    try:
        await publisher.publish(ioc)
        return {"status": "success", "message": f"IoC {ioc.value} published"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ioc/bulk")
async def submit_bulk_iocs(iocs: List[IoC]):
    results = []
    for ioc in iocs:
        try:
            await publisher.publish(ioc)
            results.append({"value": ioc.value, "status": "success"})
        except Exception as e:
            results.append({"value": ioc.value, "status": "failed", "error": str(e)})
    return {"results": results}
