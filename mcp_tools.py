from contextlib import AsyncExitStack

from google.genai import types
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from config import SERVIDORES_MCP

sessao_da_ferramenta: dict[str, ClientSession] = {}


async def conectar_servidor_mcp(pilha: AsyncExitStack, parametros) -> list:
    """Inicia um servidor MCP e devolve as ferramentas dele já no formato do Gemini."""
    leitura, escrita = await pilha.enter_async_context(stdio_client(parametros))
    sessao = await pilha.enter_async_context(ClientSession(leitura, escrita))
    await sessao.initialize()

    declaracoes = []
    for ferramenta in (await sessao.list_tools()).tools:
        sessao_da_ferramenta[ferramenta.name] = sessao
        declaracoes.append(
            types.FunctionDeclaration(
                name=ferramenta.name,
                description=ferramenta.description,
                parameters_json_schema=ferramenta.input_schema,
            )
        )
    print(f"MCP {parametros.args[1]}: {[d.name for d in declaracoes]}")
    return declaracoes


async def conectar_todos(pilha: AsyncExitStack) -> list:
    """Conecta todos os servidores de SERVIDORES_MCP e junta as ferramentas."""
    declaracoes = []
    for parametros in SERVIDORES_MCP:
        declaracoes += await conectar_servidor_mcp(pilha, parametros)
    return declaracoes


async def executar_ferramenta(nome: str, argumentos: dict) -> str:
    """Roda a ferramenta no servidor MCP dono dela. Erros viram texto para o modelo."""
    sessao = sessao_da_ferramenta.get(nome)
    if sessao is None:
        return f"A ferramenta {nome} não existe."
    try:
        resultado = await sessao.call_tool(nome, argumentos)
    except Exception as erro:
        return f"Erro ao executar {nome}: {erro}"
    texto = "\n".join(c.text for c in resultado.content if getattr(c, "text", None))
    return f"Erro: {texto}" if resultado.is_error else texto
