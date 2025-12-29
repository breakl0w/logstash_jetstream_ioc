# webhook_to_nats.py
from flask import Flask, request, jsonify
import asyncio
from nats.aio.client import Client as NATS
import json
import threading

app = Flask(__name__)

class NATSPublisher:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.nc = None
        self.js = None
        
        # Запускаем event loop в отдельном потоке
        threading.Thread(target=self._run_loop, daemon=True).start()
    
    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect())
        self.loop.run_forever()
    
    async def _connect(self):
        self.nc = NATS()
        await self.nc.connect("nats://localhost:4222")
        self.js = self.nc.jetstream()
    
    def publish(self, ioc_data):
        asyncio.run_coroutine_threadsafe(
            self._publish(ioc_data),
            self.loop
        )
    
    async def _publish(self, ioc_data):
        subject = f"ioc.{ioc_data['type']}"
        await self.js.publish(subject, json.dumps(ioc_data).encode())

publisher = NATSPublisher()

@app.route('/webhook/ioc', methods=['POST'])
def receive_ioc():
    data = request.json
    
    # Валидация
    required_fields = ['value', 'type', 'threat_type', 'source']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Публикация в NATS
    publisher.publish(data)
    
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
