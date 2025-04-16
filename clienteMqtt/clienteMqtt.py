import asyncio, ssl, certifi, logging, os
import aiomqtt

logging.basicConfig(format='%(asctime)s - %(taskName)s - cliente mqtt - %(levelname)s:%(message)s', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S %z')


async def temperature_consumer():
    while True:
        message = await temperature_queue.get()
        # print(f"[temperature/#] {message.payload}")
        logging.info(f"{message.topic}: {message.payload.decode("utf-8")}")


async def humidity_consumer():
    while True:
        message = await humidity_queue.get()
        # print(f"[humidity/#] {message.payload}")
        logging.info(f"{message.topic}: {message.payload.decode("utf-8")}")


temperature_queue = asyncio.Queue()
humidity_queue = asyncio.Queue()


async def distributor(client):
    # Sort messages into the appropriate queues
    async for message in client.messages:
        if message.topic.matches(os.environ['TOPICO1']):
            temperature_queue.put_nowait(message)
        elif message.topic.matches(os.environ['TOPICO2']):
            humidity_queue.put_nowait(message)


async def count_up(shared_resource):
    while True:
        await asyncio.sleep(3)
        shared_resource["count"] += 1


async def publisher(client, shared_resource):
    while True:
        await asyncio.sleep(5)
        await client.publish(os.environ['TOPICO3'], f"{shared_resource["count"]}", qos=0)


async def main():
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()

    shared_resource = {"count": 0}
    
    async with aiomqtt.Client(
        os.environ['SERVIDOR'],
        port=8883,
        tls_context=tls_context,
    ) as client:
        await client.subscribe(os.environ["TOPICO1"])
        await client.subscribe(os.environ["TOPICO2"])
        # Use a task group to manage and await all tasks
        async with asyncio.TaskGroup() as tg:
            tg.create_task(distributor(client))
            tg.create_task(temperature_consumer())
            tg.create_task(humidity_consumer())
            tg.create_task(count_up(shared_resource))
            tg.create_task(publisher(client, shared_resource))


if __name__ == "__main__":
    asyncio.run(main())
