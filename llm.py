from google import genai
from google.genai import types

from config import GEMINI_MODEL, MAX_CHAMADAS_TOOL, SYSTEM_INSTRUCTION
from mcp_tools import executar_ferramenta

gemini = genai.Client()  # lê GEMINI_API_KEY do ambiente
config_gemini: types.GenerateContentConfig | None = None  # montada em configurar()


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
        resposta = await gemini.aio.models.generate_content(
            model=GEMINI_MODEL, contents=historico, config=config_gemini
        )
        if not resposta.candidates or not resposta.candidates[0].content:
            raise RuntimeError("O modelo não devolveu resposta.")
        historico.append(resposta.candidates[0].content)

        # 1. O modelo respondeu com texto: acabou.
        if not resposta.function_calls:
            return resposta.text or "Não consegui responder. Tente reformular.", usadas

        # 2. O modelo pediu ferramentas: o NOSSO código executa no servidor MCP...
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
        # 3. ...e devolve o resultado para o modelo continuar.
        historico.append(types.Content(role="user", parts=partes))

    return "Precisei de ferramentas demais nessa pergunta. Tente simplificar.", usadas
