import asyncio

# from amqtt.client import MQTTClient
from amqtt.broker import Broker, BrokerConfig, ListenerConfig
from config import Config

config = BrokerConfig(
    listeners={
    "default": ListenerConfig(
            bind=f"{Config.host}:{Config.port}",
            max_connections=3
        )
    },
    timeout_disconnect_delay=10
)

async def start():
    broker = Broker(config)
    try:
        await broker.start()
        print(f"Broker started on {Config.host}:{Config.port} successfully.")
        print("Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await broker.shutdown()
        print("Shutdown\n")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    asyncio.run(start())