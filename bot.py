import asyncio
from contextlib import AsyncExitStack

import llm
from config import DISCORD_TOKEN
from discord_bot import bo
from mcp_tools import conectar_todos


async def main():
    async with AsyncExitStack() as pilha:
        llm.configurar(await conectar_todos(pilha))

        async with bot:
            await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
