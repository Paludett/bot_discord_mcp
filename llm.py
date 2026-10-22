import asyncio

from google import genai
from google.genai import errors, types

from config import (
    GEMINI_MODEL,
    GEMINI_MODEL_RESERVA,
    MAX_CHAMADAS_TOOL,
    SYSTEM_INSTRUCTION,
    TENTATIVAS_POR_MODELO,
)
from mcp_tools import executar_ferramenta

gemini = genai.Client()
config_gemini: types.GenerateContentConfig | None = None


def _passageiro(erro: errors.APIError) -> bool:
    return erro.code == 429 or erro.code >= 500


async def gerar(historico: list[types.Content]):
    modelos = [GEMINI_MODEL]
    if GEMINI_MODEL_RESERVA and GEMINI_MODEL_RESERVA != GEMINI_MODEL:
        modelos.append(GEMINI_MODEL_RESERVA)

    for i, modelo in enumerate(modelos):
        for tentativa in range(TENTATIVAS_POR_MODELO):
            try:
                return await gemini.aio.models.generate_content(
                    model=modelo, contents=historico, config=config_gemini
                )
            except errors.APIError as erro:
                if not _passageiro(erro):
                    raise
                ultimo_modelo = i == len(modelos) - 1
                ultima_tentativa = tentativa == TENTATIVAS_POR_MODELO - 1
                print(f"  {modelo}: {erro.code} (tentativa {tentativa + 1})")
                if ultimo_modelo and ultima_tentativa:
                    raise
                if not ultima_tentativa:
                    await asyncio.sleep(2**tentativa)


def configurar(declaracoes: list) -> None:
    global config_gemini
    config_gemini = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[types.Tool(function_declarations=declaracoes)],
    )


async def responder(historico: list[types.Content]) -> tuple[str, list[str]]:
    """Laço de tool calling. Devolve o texto final e as ferramentas usadas."""
    usadas = []
    for _ in range(MAX_CHAMADAS_TOOL + 1):
        resposta = await gerar(historico)
        if not resposta.candidates or not resposta.candidates[0].content:
            raise RuntimeError("O modelo não devolveu resposta.")
        historico.append(resposta.candidates[0].content)

        if not resposta.function_calls:
            return resposta.text or "Não consegui responder. Tente reformular.", usadas

        partes = []
        for chamada in resposta.function_calls:
            usadas.append(chamada.name)
            print(f"  -> {chamada.name}({dict(chamada.args or {})})")
            resultado = await executar_ferramenta(chamada.name, dict(chamada.args or {}))
            partes.append(
                types.Part.from_function_response(
                    name=chamada.name, response={"resultado": resultado}
                )
            )
        historico.append(types.Content(role="user", parts=partes))

    return "Precisei de ferramentas demais nessa pergunta. Tente simplificar.", usadas
