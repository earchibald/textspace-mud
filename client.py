#!/usr/bin/env python3
import asyncio
import sys

async def client():
    reader, writer = await asyncio.open_connection('localhost', 8888)
    
    async def read_from_server():
        while True:
            try:
                data = await reader.read(1024)
                if not data:
                    break
                sys.stdout.write(data.decode())
                sys.stdout.flush()
            except:
                break
    
    async def write_to_server():
        while True:
            try:
                message = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not message:
                    break
                writer.write(message.encode())
                await writer.drain()
            except:
                break
    
    # Start both tasks
    await asyncio.gather(
        read_from_server(),
        write_to_server(),
        return_exceptions=True
    )
    
    writer.close()

if __name__ == "__main__":
    try:
        asyncio.run(client())
    except KeyboardInterrupt:
        print("\nDisconnected.")
