"""
Bot do Discord do Treinador Virtual de LoL - Versão Cloud

Esta versão suporta:
- Múltiplos servidores Discord simultaneamente
- Integração com WebSocket server para receber dados de clientes locais
- Sistema de tokens de autenticação por usuário
- Gerenciamento de estado por servidor (guild)
"""

import discord
from discord.ext import commands, tasks
import asyncio
import os
from pathlib import Path
from openai import OpenAI
from gtts import gTTS
import io
import sys
import requests
from typing import Dict

# Importar o servidor WebSocket
from websocket_server import WebSocketServer

# Importar módulos do treinador
sys.path.insert(0, os.path.dirname(__file__))
from analysis_and_tips_module_cloud import GameAnalyzer

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=\'!coach \', intents=intents)

# Chave da Riot API
RIOT_API_KEY = os.getenv("RIOT_API_KEY")

# Estado por servidor (guild)
class GuildState:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.monitoring = False
        self.voice_client = None
        self.game_analyzer = GameAnalyzer()
        self.monitored_players = []
        self.last_tips = []
        self.audio_queue = asyncio.Queue()
        self.bot_name = "Treinador Virtual"
        self.text_channel = None  # Canal onde o bot foi ativado
        self.user_tokens = {}  # user_id -> token

# Dicionário de estados por servidor
bot.guild_states: Dict[int, GuildState] = {}

# Servidor WebSocket
ws_server = None

def get_guild_state(guild_id: int) -> GuildState:
    """Obtém ou cria o estado para um servidor"""
    if guild_id not in bot.guild_states:
        bot.guild_states[guild_id] = GuildState(guild_id)
    return bot.guild_states[guild_id]

# Eventos do bot
@bot.event
async def on_ready():
    """Evento chamado quando o bot está pronto"""
    print(f"✅ Bot conectado como {bot.user}")
    print(f"📊 Servidores: {len(bot.guilds)}")
    print(f"🔗 Link de convite: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=3165184&scope=bot")
    
    # Inicializar estados para todos os servidores
    for guild in bot.guilds:
        get_guild_state(guild.id)
    
    # Iniciar o servidor WebSocket
    global ws_server
    ws_server = WebSocketServer(bot)
    asyncio.create_task(ws_server.start(host="0.0.0.0", port=8765))

@bot.event
async def on_guild_join(guild):
    """Evento chamado quando o bot entra em um novo servidor"""
    print(f"✅ Bot adicionado ao servidor: {guild.name} (ID: {guild.id})")
    get_guild_state(guild.id)
    
    # Enviar mensagem de boas-vindas
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send(
                f"👋 Olá! Eu sou o **Treinador Virtual de League of Legends**!\n\n"
                f"Para começar a usar, siga estes passos:\n"
                f"1. Use `!coach gettoken` para obter seu token de autenticação\n"
                f"2. Baixe e execute o cliente local: [Link do Cliente (Em Breve)]\n"
                f"3. Entre em um canal de voz e use `!coach join`\n"
                f"4. Use `!coach start` para iniciar o monitoramento\n\n"
                f"Use `!coach help` para ver todos os comandos disponíveis!"
            )
            break

@bot.event
async def on_guild_remove(guild):
    """Evento chamado quando o bot sai de um servidor"""
    print(f"❌ Bot removido do servidor: {guild.name} (ID: {guild.id})")
    if guild.id in bot.guild_states:
        del bot.guild_states[guild.id]

# Comandos do bot

@bot.command(name=\'gettoken\', help=\'Obtém seu token de autenticação para o cliente local\')
async def get_token(ctx):
    """Gera e envia um token de autenticação para o usuário"""
    guild_state = get_guild_state(ctx.guild.id)
    
    # Gerar token
    token = ws_server.generate_token(ctx.author.id, ctx.guild.id, ctx.author.display_name)
    guild_state.user_tokens[ctx.author.id] = token
    
    # Enviar token via DM
    try:
        await ctx.author.send(
            f"🔑 **Seu Token de Autenticação**\n\n"
            f"```\n{token}\n```\n\n"
            f"⚠️ **Importante:**\n"
            f"- Não compartilhe este token com ninguém\n"
            f"- Use este token para configurar a variável de ambiente `USER_AUTH_TOKEN` no cliente local\n"
            f"- O token é válido por 30 dias\n\n"
            f"📥 **Como usar:**\n"
            f"1. Baixe o cliente local (link em breve)\n"
            f"2. Configure a variável `USER_AUTH_TOKEN` com este token\n"
            f"3. Execute o cliente local antes de jogar"
        )
        await ctx.send(f"✅ {ctx.author.mention}, enviei seu token por mensagem privada!")
    except discord.Forbidden:
        await ctx.send(
            f"❌ {ctx.author.mention}, não consegui enviar uma mensagem privada. "
            f"Por favor, habilite mensagens privadas de membros do servidor."
        )

@bot.command(name=\'join\', help=\'O bot entra no seu canal de voz\')
async def join(ctx):
    """Faz o bot entrar no canal de voz do usuário"""
    guild_state = get_guild_state(ctx.guild.id)
    
    if not ctx.author.voice:
        await ctx.send("❌ Você precisa estar em um canal de voz!")
        return
    
    channel = ctx.author.voice.channel
    
    if guild_state.voice_client and guild_state.voice_client.is_connected():
        await guild_state.voice_client.move_to(channel)
    else:
        guild_state.voice_client = await channel.connect()
    
    await ctx.send(f"✅ Conectado ao canal **{channel.name}**!")

@bot.command(name=\'leave\', help=\'O bot sai do canal de voz\')
async def leave(ctx):
    """Faz o bot sair do canal de voz"""
    guild_state = get_guild_state(ctx.guild.id)
    
    if guild_state.voice_client and guild_state.voice_client.is_connected():
        await guild_state.voice_client.disconnect()
        guild_state.voice_client = None
        await ctx.send("👋 Desconectado do canal de voz!")
    else:
        await ctx.send("❌ Não estou em nenhum canal de voz!")

@bot.command(name=\'start\', help=\'Inicia o monitoramento da partida\')
async def start_monitoring(ctx):
    """Inicia o monitoramento da partida"""
    guild_state = get_guild_state(ctx.guild.id)
    
    if guild_state.monitoring:
        await ctx.send("⚠️ O monitoramento já está ativo!")
        return
    
    guild_state.monitoring = True
    guild_state.text_channel = ctx.channel
    guild_state.last_tips = []
    
    await ctx.send(
        f"✅ Monitoramento iniciado!\n\n"
        f"📱 **Certifique-se de que:**\n"
        f"1. O cliente local está rodando no seu computador\n"
        f"2. Você está em uma partida do League of Legends\n\n"
        f"💡 Vou fornecer dicas em tempo real via voz e texto!"
    )

@bot.command(name=\'stop\', help=\'Para o monitoramento da partida\')
async def stop_monitoring(ctx):
    """Para o monitoramento da partida"""
    guild_state = get_guild_state(ctx.guild.id)
    
    if not guild_state.monitoring:
        await ctx.send("⚠️ O monitoramento não está ativo!")
        return
    
    guild_state.monitoring = False
    guild_state.last_tips = []
    
    await ctx.send("⏹️ Monitoramento parado!")

@bot.command(name=\'setname\', help=\'Define um nome personalizado para o treinador\')
async def set_bot_name(ctx, *, new_name: str):
    """Define um nome personalizado para o treinador"""
    guild_state = get_guild_state(ctx.guild.id)
    guild_state.bot_name = new_name
    await ctx.send(f"✅ Meu nome agora é **{new_name}**! Prazer em conhecê-lo, {ctx.author.display_name}.")

@bot.command(name=\'ask\', help=\'Faz uma pergunta ao treinador\')
async def ask(ctx, *, question: str):
    """Responde a uma pergunta do usuário"""
    guild_state = get_guild_state(ctx.guild.id)
    await ctx.send("🤔 Pensando...")
    
    try:
        # Obter contexto do jogo do cliente local, se disponível
        user_token = guild_state.user_tokens.get(ctx.author.id)
        game_data = ws_server.active_games.get(user_token) if user_token else None
        
        context = ""
        if game_data:
            active_player = game_data.get("activePlayer", {})
            player_list = game_data.get("allPlayers", [])
            game_stats = game_data.get("gameData", {})
            
            if active_player:
                context += f"O jogador ativo é {active_player.get(\'summonerName\')} jogando com {active_player.get(\'championName\')}. "
                context += f"Ele está no nível {active_player.get(\'level\')} e tem {active_player.get(\'currentGold\')} de ouro. "
            if game_stats:
                context += f"O tempo de jogo atual é de {game_stats.get(\'gameTime\')} segundos. "
            if player_list:
                context += f"Os campeões no jogo são: {\', \'.join([p.get(\'championName\') for p in player_list])}. "
        
        # Preparar mensagem para o LLM
        openai_client = OpenAI()
        messages = [
            {"role": "system", "content": f"Você é um treinador virtual de League of Legends chamado {guild_state.bot_name}. Forneça dicas e responda a perguntas de forma útil e concisa, baseando-se no contexto do jogo fornecido. Use português do Brasil. Mantenha um tom de coach profissional e encorajador. Ao se dirigir ao usuário, use o nome dele: {ctx.author.display_name}."},
        ]
        if context:
            messages.append({"role": "system", "content": f"Contexto atual do jogo: {context}"})
        messages.append({"role": "user", "content": question})
        
        response = openai_client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=messages,
            max_tokens=150
        )
        
        answer = response.choices[0].message.content
        
        # Enviar resposta no chat
        await ctx.send(f"💡 **{guild_state.bot_name} diz:**\n{answer}")
        
        # Se estiver em um canal de voz, também falar a resposta
        if guild_state.voice_client and guild_state.voice_client.is_connected():
            await speak_text(guild_state, answer)
    
    except Exception as e:
        await ctx.send(f"❌ Erro ao processar pergunta: {str(e)}")

@bot.command(name=\'status\', help=\'Mostra o status do monitoramento\')
async def status(ctx):
    """Mostra o status do monitoramento"""
    guild_state = get_guild_state(ctx.guild.id)
    
    status_msg = f"📊 **Status do {guild_state.bot_name}**\n\n"
    status_msg += f"🎤 Canal de voz: {\'Conectado\' if guild_state.voice_client and guild_state.voice_client.is_connected() else \'Desconectado\'}\n"
    status_msg += f"👁️ Monitoramento: {\'Ativo ✅\' if guild_state.monitoring else \'Inativo ⏸️\'}\n"
    
    connected_clients_count = len([t for t, info in ws_server.user_tokens.items() if info["guild_id"] == ctx.guild.id and t in ws_server.clients])
    status_msg += f"🔗 Clientes locais conectados: {connected_clients_count}\n"
    
    await ctx.send(status_msg)

# Função para obter PUUID de um nome de invocador
async def get_puuid_by_summoner_name(summoner_name: str, region: str = "br1"):
    if not RIOT_API_KEY:
        print("RIOT_API_KEY não configurada.")
        return None
    
    # Primeiro, obter o summonerId
    summoner_url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={RIOT_API_KEY}"
    try:
        response = requests.get(summoner_url)
        response.raise_for_status() # Levanta exceção para erros HTTP
        summoner_data = response.json()
        return summoner_data.get("puuid")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter PUUID para {summoner_name}: {e}")
        return None

# Função para obter match IDs
async def get_match_ids_by_puuid(puuid: str, count: int = 1, region_routing: str = "americas"):
    if not RIOT_API_KEY:
        print("RIOT_API_KEY não configurada.")
        return []
    
    match_list_url = f"https://{region_routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}&api_key={RIOT_API_KEY}"
    try:
        response = requests.get(match_list_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter match IDs para PUUID {puuid}: {e}")
        return []

# Função para obter detalhes da partida
async def get_match_details(match_id: str, region_routing: str = "americas"):
    if not RIOT_API_KEY:
        print("RIOT_API_KEY não configurada.")
        return None
    
    match_details_url = f"https://{region_routing}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={RIOT_API_KEY}"
    try:
        response = requests.get(match_details_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter detalhes da partida {match_id}: {e}")
        return None

# Função para gerar relatório pós-partida (agora no bot_cloud)
def generate_postgame_report(match_details: dict, player_puuid: str, bot_name: str) -> str:
    """Gera um relatório de análise pós-partida a partir dos detalhes da partida."""
    report = []

    # Carregar dados de itens para nomes
    item_data = {}
    try:
        item_file = os.path.join(os.path.dirname(__file__), "item.json")
        with open(item_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            item_data = {item_id: item_info["name"] for item_id, item_info in data["data"].items()}
    except FileNotFoundError:
        print("Erro: item.json não encontrado para análise pós-partida.")
    except Exception as e:
        print(f"Erro ao carregar dados de itens para análise pós-partida: {e}")

    # Encontrar o participante do jogador
    player_participant = None
    for participant in match_details["info"]["participants"]:
        if participant["puuid"] == player_puuid:
            player_participant = participant
            break

    if not player_participant:
        return "Não foi possível encontrar os dados do jogador nesta partida."

    # Resumo da partida
    game_duration_seconds = match_details["info"]["gameDuration"]
    game_duration_minutes = round(game_duration_seconds / 60)
    game_mode = match_details["info"]["gameMode"]
    win = "Vitória" if player_participant["win"] else "Derrota"

    report.append(f"**Resultado:** {win} em {game_mode} ({game_duration_minutes} minutos)")
    report.append(f"**Campeão:** {player_participant["championName"]} ({player_participant["champLevel"]}) - KDA: {player_participant["kills"]}/{player_participant["deaths"]}/{player_participant["assists"]}")
    report.append(f"**Farm (CS):** {player_participant["totalMinionsKilled"]} + {player_participant["neutralMinionsKilled"]} (selva)")
    report.append(f"**Ouro:** {round(player_participant["goldEarned"] / 1000, 1)}k")
    report.append(f"**Dano Causado:** {player_participant["totalDamageDealtToChampions"]:,}")
    report.append(f"**Visão:** {player_participant["visionScore"]}")

    # Análise de itens
    items_names = []
    for i in range(0, 7): # Itens de 0 a 6
        item_id = player_participant.get(f"item{i}")
        if item_id and item_id != 0:
            item_name = item_data.get(str(item_id), f"Item ID: {item_id}")
            items_names.append(item_name)
    if items_names:
        report.append(f"**Itens Finais:** {\", \".join(items_names)}")

    # Dicas baseadas em performance
    if player_participant["deaths"] > player_participant["kills"] + player_participant["assists"]:
        report.append("💡 **Dica:** Você teve muitas mortes em relação aos abates e assistências. Tente jogar de forma mais segura e evitar lutas desfavoráveis.")
    elif player_participant["totalMinionsKilled"] < (game_duration_minutes * 5): # Exemplo: menos de 5 CS por minuto
        report.append("💡 **Dica:** Seu farm (CS) foi um pouco baixo. Focar em farmar mais pode te dar uma vantagem de ouro significativa.")
    
    if player_participant["visionScore"] < (game_duration_minutes * 1.5): # Exemplo: menos de 1.5 de visão por minuto
        report.append("💡 **Dica:** Sua pontuação de visão foi um pouco baixa. Wards são cruciais para controle de mapa e segurança.")

    # Dicas do LLM para análise mais aprofundada
    try:
        openai_client = OpenAI()
        llm_prompt = f"Analise o seguinte desempenho de um jogador em uma partida de League of Legends e forneça dicas construtivas e personalizadas. O jogador jogou de {player_participant["championName"]}. KDA: {player_participant["kills"]}/{player_participant["deaths"]}/{player_participant["assists"]}. Farm: {player_participant["totalMinionsKilled"]} + {player_participant["neutralMinionsKilled"]}. Ouro: {round(player_participant["goldEarned"] / 1000, 1)}k. Dano: {player_participant["totalDamageDealtToChampions"]:,}. Visão: {player_participant["visionScore"]}. Itens: {\", \".join(items_names)}. A partida durou {game_duration_minutes} minutos e o resultado foi {win}. O que o jogador poderia ter feito melhor e quais são 2-3 dicas acionáveis para a próxima partida?" 
        
        llm_response = openai_client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": f"Você é um treinador de League of Legends chamado {bot_name}. Forneça análises pós-partida detalhadas e dicas construtivas. Use português do Brasil."},
                {"role": "user", "content": llm_prompt}
            ],
            max_tokens=300
        )
        llm_tip = llm_response.choices[0].message.content
        report.append(f"\n🧠 **Análise Avançada do {bot_name}:**\n{llm_tip}")

    except Exception as e:
        print(f"Erro ao gerar análise pós-partida com LLM: {e}")
        report.append("\n⚠️ Não foi possível gerar uma análise avançada no momento.")

    return "\n".join(report)

@bot.command(name=\'postgame\', help=\'Analisa a última partida de um jogador (uso: !coach postgame NomeInvocador)\')
async def postgame_analysis(ctx, *, summoner_name: str):
    """Realiza a análise pós-partida para um jogador"""
    guild_state = get_guild_state(ctx.guild.id)
    await ctx.send(f"🔎 {guild_state.bot_name} está analisando a última partida de **{summoner_name}**... Isso pode levar um momento.")

    try:
        # 1. Obter PUUID do nome de invocador
        puuid = await get_puuid_by_summoner_name(summoner_name)
        if not puuid:
            await ctx.send(f"❌ {guild_state.bot_name} não conseguiu encontrar o PUUID para **{summoner_name}**. Verifique o nome e a região (padrão: br1).")
            return

        # 2. Obter IDs das últimas partidas
        # Assumindo que a região de roteamento para BR é \'americas\'
        match_ids = await get_match_ids_by_puuid(puuid, count=1, region_routing="americas")
        if not match_ids:
            await ctx.send(f"❌ {guild_state.bot_name} não encontrou nenhuma partida recente para **{summoner_name}**.")
            return

        latest_match_id = match_ids[0]

        # 3. Obter detalhes da última partida
        match_details = await get_match_details(latest_match_id, region_routing="americas")
        if not match_details:
            await ctx.send(f"❌ {guild_state.bot_name} não conseguiu obter os detalhes da partida {latest_match_id}.")
            return

        # 4. Processar e gerar análise
        analysis_report = generate_postgame_report(match_details, puuid, guild_state.bot_name)

        await ctx.send(f"✅ **Análise Pós-Partida de {guild_state.bot_name} para {summoner_name} (Partida ID: {latest_match_id}):**\n\n{analysis_report}")

        if guild_state.voice_client and guild_state.voice_client.is_connected():
            await speak_text(guild_state, f"Análise pós-partida para {summoner_name} concluída. Verifique o chat para o relatório completo.")

    except Exception as e:
        await ctx.send(f"❌ Ocorreu um erro durante a análise pós-partida: {str(e)}")

async def speak_text(guild_state: GuildState, text: str):
    """Converte texto em fala e reproduz no canal de voz do Discord"""
    if not guild_state.voice_client or not guild_state.voice_client.is_connected():
        return
    
    try:
        # Gerar áudio usando gTTS
        tts = gTTS(text=text, lang='pt', slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Aguardar se já estiver falando
        while guild_state.voice_client.is_playing():
            await asyncio.sleep(0.1)
        
        # Reproduzir áudio
        audio_source = discord.FFmpegPCMAudio(fp)
        guild_state.voice_client.play(audio_source)
        
        # Aguardar término da reprodução
        while guild_state.voice_client.is_playing():
            await asyncio.sleep(0.1)
        
        fp.close()
    
    except Exception as e:
        print(f"Erro ao falar texto: {e}")

# Adicionar speak_text como método do bot para acesso do WebSocket server
bot.speak_text = speak_text

# Comandos de encerramento
@bot.command(name=\'shutdown\', help=\'Desliga o bot (apenas para usuários autorizados)\'
)
async def shutdown(ctx):
    """Desliga o bot"""
    # Apenas o dono do bot pode desligá-lo
    if ctx.author.id == bot.owner_id:
        await ctx.send("👋 Desligando o treinador virtual. Até a próxima!")
        await bot.close()
    else:
        await ctx.send("❌ Você não tem permissão para desligar o bot.")

# Executar o bot
if __name__ == "__main__":
    DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    
    if not DISCORD_TOKEN:
        print("❌ ERRO: Token do Discord não configurado!")
        print("Por favor, configure a variável de ambiente DISCORD_BOT_TOKEN")
        exit(1)
    
    # Obter o ID do dono do bot (para o comando shutdown)
    # Isso geralmente é configurado no Discord Developer Portal
    # Ou pode ser o ID do usuário que está executando o bot localmente
    bot.owner_id = int(os.getenv("DISCORD_OWNER_ID", 0)) # Defina DISCORD_OWNER_ID no .env

    print("🚀 Iniciando o Treinador Virtual (Versão Cloud)...")
    bot.run(DISCORD_TOKEN)

