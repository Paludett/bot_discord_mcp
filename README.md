# Bot MCP — exemplo da oficina de bots de IA no Discord

O mesmo bot da aula (responde quando é mencionado, lembra a conversa do canal,
cooldown de 5 s, corte em 2000 caracteres), agora com **tool calling via MCP**.
Em vez de escrever as funções na mão, ele usa dois servidores MCP prontos:

| Servidor | Ferramentas | Para quê |
|---|---|---|
| `mcp-server-time` | `get_current_time`, `convert_time` | hora atual e fusos horários |
| `mcp-server-fetch` | `fetch` | baixar uma página e ler o conteúdo |

Os servidores rodam como subprocessos (stdio) dentro do próprio bot. Cada
resposta mostra no rodapé quais ferramentas o modelo usou.

## Rodando no seu PC

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env             # Windows: Copy-Item .env.example .env
python bot.py
```

Deu certo quando aparecer `Online como ...`. No Developer Portal, o bot precisa
da **Message Content Intent** ligada.

## Deploy no Railway

1. No projeto do Railway: **+ Create → GitHub Repo** → este repositório.
   O `railway.toml` já manda usar o Dockerfile.
2. Em **Variables**: `DISCORD_TOKEN` e
   `GEMINI_API_KEY=${{shared.GEMINI_API_KEY}}`.
3. Não precisa de domínio público, porta nem volume.

## Perguntas para a demo

- `@bot que horas são agora?`: sem a ferramenta, o modelo não tem como saber.
- `@bot quando for 19h aqui, que horas vão ser em Lisboa e em Tóquio?`
- `@bot resume essa página: <link>`

## Bom saber

- **robots.txt:** o Fetch respeita o robots.txt, então alguns sites recusam.
  Teste o link da demo antes da aula.
- **Fuso:** o container roda em UTC; o fuso local vem de `FUSO_HORARIO`.
- **Segurança:** o texto de uma página baixada pode tentar dar ordens ao modelo
  (*prompt injection*). O `system_instruction` avisa para não obedecer, mas isso
  reduz o risco sem eliminar. Por isso o bot só tem ferramentas de leitura.
- **Node.js é opcional:** sem ele, o Fetch extrai o texto em modo Python puro e
  só imprime um aviso no log.
