'''
KKuTu on Discord - A bot for the KKuTu game

TODO:
- [ ] 게임 진행 로직 구현
- - 기타 게임 유틸리티
- - - [ ] 단어 검색 기능
- [ ] 게임 상태 관리
- [ ] 사용자 인터랙션 처리
- [ ] 에러 핸들링 및 예외 처리
- 추가 명령어 및 기능 구현
- - [ ] 언어 추가
- [ ] 테스트 및 디버깅

db.json 구조:
kkutu_ko: [
_id: 단어,
type: 단어 유형 [
	"class_1": "명",
	"class_2": "대명",
	"class_3": "수",
	"class_4": "조",
	"class_5": "동",
	"class_6": "형",
	"class_7": "관",
	"class_8": "부",
	"class_9": "감",
	"class_10": "접",
	"class_11": "의명",
	"class_12": "조동",
	"class_13": "조형",
	"class_14": "어",
	"class_15": "관·명",
	"class_16": "수·관",
	"class_17": "명·부",
	"class_18": "감·명",
	"class_19": "대·부",
	"class_20": "대·감",
	"class_21": "동·형",
	"class_22": "관·감",
	"class_23": "부·감",
	"class_24": "의명·조",
	"class_25": "수·관·명",
	"class_26": "대·관"
],
hit: 단어가 사용된 횟수,
flag: 단어 종류[
	LOANWORD: 1, # 외래어
	INJEONG: 2, # 어인정
	SPACED: 4, # 띄어쓰기를 해야 하는 어휘
	SATURI: 8, # 방언
	OLD: 16, # 옛말
	MUNHWA: 32 # 문화어
]
theme: 단어의 테마 [
	"theme_e03": "★",
	"theme_e05": "동물",
	"theme_e08": "인체",
	"theme_e12": "감정",
	"theme_e13": "음식",
	"theme_e15": "지명",
	"theme_e18": "사람",
	"theme_e20": "식물",
	"theme_e43": "날씨",
	"theme_10": "가톨릭",
	"theme_20": "건설",
	"theme_30": "경제",
	"theme_40": "고적",
	"theme_50": "고유",
	"theme_60": "공업",
	"theme_70": "광업",
	"theme_80": "교육",
	"theme_90": "교통",
	"theme_100": "군사",
	"theme_110": "기계",
	"theme_120": "기독교",
	"theme_130": "논리",
	"theme_140": "농업",
	"theme_150": "문학",
	"theme_160": "물리",
	"theme_170": "미술",
	"theme_180": "민속",
	"theme_190": "동물",
	"theme_200": "법률",
	"theme_210": "불교",
	"theme_220": "사회",
	"theme_230": "생물",
	"theme_240": "수학",
	"theme_250": "수산",
	"theme_260": "수공",
	"theme_270": "식물",
	"theme_280": "심리",
	"theme_290": "약학",
	"theme_300": "언론",
	"theme_310": "언어",
	"theme_320": "역사",
	"theme_330": "연영",
	"theme_340": "예술",
	"theme_350": "운동",
	"theme_360": "음악",
	"theme_370": "의학",
	"theme_380": "인명",
	"theme_390": "전기",
	"theme_400": "정치",
	"theme_410": "종교",
	"theme_420": "지리",
	"theme_430": "지명",
	"theme_440": "책명",
	"theme_450": "천문",
	"theme_460": "철학",
	"theme_470": "출판",
	"theme_480": "통신",
	"theme_490": "컴퓨터",
	"theme_500": "한의학",
	"theme_510": "항공",
	"theme_520": "해양",
	"theme_530": "화학",
	"theme_1001": "나라 이름과 수도"
]
'''
import json
import os
import re
import datetime
import random
import logging
import sys

from util.db import SearchDB, Getmean, CheckDB, SearchByChar, SearchMissionWords, SearchRandomWords
from util.meanutil import format_mean_text, format_theme_text, format_type_text, format_flag_text
from util.langutil import check_language_keys, getlang
from util.regexutil import isRegexSafe
from util.commandutil import detect_language, parse_meaning, format_word, count_char_occurrences, VALID_WORD_CHARS
from util.roomutil import build_option_summary_lines, ROOM_OPTION_VALUES, get_room_option_catalog

import discord
from discord.ext import commands


logging.basicConfig(
	level=logging.INFO,
	format='[%(asctime)s] %(message)s',
	datefmt='%H:%M:%S',
	stream=sys.stdout,
)
logger = logging.getLogger(__name__)


intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)

global SETTINGS, DB_PATH, LANGUAGE_PATH, SEARCH_LIMIT, WHAT_IS_THIS_SETTING, WHAT_IS_THIS_LIST, WHAT_IS_THIS_LIST2, LANGUAGE_DICT, PGSQL_CONFIG, USE_PGSQL
try:
	with open("settings.json", "r", encoding="utf-8") as f:
		SETTINGS = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
	logger.error(f"Failed to load settings.json: {e}")
	SETTINGS = {}

DB_PATH = SETTINGS.get("DB_PATH", "db.json")
LANGUAGE_PATH = SETTINGS.get("LANGUAGE_PATH", "ko_kr.json")
SEARCH_LIMIT = SETTINGS.get("SEARCH_RESULT_LIMIT", 20)
PGSQL_CONFIG = SETTINGS.get("PGSQL_CONFIG", {})
USE_PGSQL = bool(PGSQL_CONFIG.get("USE_PGSQL", False))
MAX_RANDOM_COUNT = 50
WHAT_IS_THIS_SETTING = SETTINGS.get("WHAT_IS_THIS_SETTING", False)
WHAT_IS_THIS_LIST = SETTINGS.get("WHAT_IS_THIS_LIST", [])
WHAT_IS_THIS_LIST2 = SETTINGS.get("WHAT_IS_THIS_LIST2", [])
ROOM_SESSIONS: dict[int, dict] = {}

missing_keys = check_language_keys(LANGUAGE_PATH, "util/lang_keys.json")
if missing_keys:
	logger.error("Missing language keys:")
	for key in missing_keys:
		logger.error(f" - {key}")
		exit(1)
else:
	with open(LANGUAGE_PATH, "r", encoding="utf-8") as f:
		LANGUAGE_DICT = json.load(f)
	
	langpack_info = LANGUAGE_DICT.get("langpack-info", {})
	logger.info("All language keys are present.")
	logger.info(f"Language Pack: {langpack_info.get('langpack-name', 'Unknown')}")
	logger.info(f"Description: {langpack_info.get('langpack-description', 'No description available')}")

def listwords(word: list):
	result = ""
	for i, w in enumerate(word[:SEARCH_LIMIT + 1], start=1):
		result += f"{i}. {w}\n"
	return result


def _render_room_embed(session: dict) -> discord.Embed:
	players = session.get("players", {})
	player_mentions = [f"<@{uid}>" for uid in players.keys()]
	player_text = "\n".join(player_mentions) if player_mentions else getlang(LANGUAGE_DICT, "RoomPlayersEmpty")

	options = session.get("options", [])
	option_lines = build_option_summary_lines(options, LANGUAGE_DICT)
	option_text = "\n".join(option_lines) if option_lines else getlang(LANGUAGE_DICT, "RoomOptionNone")

	embed = discord.Embed(
		title=getlang(LANGUAGE_DICT, "RoomMakeTitle").format(room=session.get("name", "-")),
		description=getlang(LANGUAGE_DICT, "RoomMakeDescription"),
		color=discord.Color.orange(),
		timestamp=datetime.datetime.now(),
	)
	embed.add_field(name=getlang(LANGUAGE_DICT, "RoomFieldHost"), value=f"<@{session.get('host_id')}>", inline=True)
	embed.add_field(name=getlang(LANGUAGE_DICT, "RoomFieldMode"), value=str(session.get("mode", "-")), inline=True)
	embed.add_field(name=getlang(LANGUAGE_DICT, "RoomFieldRule"), value=f"{session.get('round', 0)}R / {session.get('time', 0)}s", inline=True)
	embed.add_field(name=getlang(LANGUAGE_DICT, "RoomFieldPlayers").format(count=len(players), limit=session.get("limit", 0)), value=player_text, inline=False)
	embed.add_field(name=getlang(LANGUAGE_DICT, "RoomFieldOptions"), value=option_text, inline=False)
	return embed


class RoomJoinView(discord.ui.View):
	def __init__(self, thread_id: int):
		super().__init__(timeout=None)
		self.thread_id = thread_id

	@discord.ui.button(label=getlang(LANGUAGE_DICT, "RoomJoinButton"), style=discord.ButtonStyle.success, custom_id="room_join")
	async def join_button(self, button: discord.ui.Button, interaction: discord.Interaction):
		session = ROOM_SESSIONS.get(self.thread_id)
		if not session:
			await interaction.response.send_message(getlang(LANGUAGE_DICT, "RoomSessionClosed"), ephemeral=True)
			return

		user_id = interaction.user.id
		if user_id in session["players"]:
			await interaction.response.send_message(getlang(LANGUAGE_DICT, "RoomAlreadyJoined"), ephemeral=True)
			return

		if len(session["players"]) >= session["limit"]:
			await interaction.response.send_message(getlang(LANGUAGE_DICT, "RoomIsFull"), ephemeral=True)
			return

		session["players"][user_id] = interaction.user.display_name
		embed = _render_room_embed(session)
		message = interaction.message
		if message:
			await message.edit(embed=embed, view=self)

		thread = interaction.channel
		if isinstance(thread, discord.Thread):
			await thread.add_user(interaction.user)

		await interaction.response.send_message(getlang(LANGUAGE_DICT, "RoomJoinSuccess").format(user=interaction.user.mention), ephemeral=True)

	@discord.ui.button(label=getlang(LANGUAGE_DICT, "RoomLeaveButton"), style=discord.ButtonStyle.danger, custom_id="room_leave")
	async def leave_button(self, button: discord.ui.Button, interaction: discord.Interaction):
		session = ROOM_SESSIONS.get(self.thread_id)
		if not session:
			await interaction.response.send_message(getlang(LANGUAGE_DICT, "RoomSessionClosed"), ephemeral=True)
			return

		user_id = interaction.user.id
		if user_id not in session["players"]:
			await interaction.response.send_message(getlang(LANGUAGE_DICT, "RoomNotJoined"), ephemeral=True)
			return

		session["players"].pop(user_id, None)

		# If no players remain, close thread and cleanup session.
		if len(session["players"]) == 0:
			ROOM_SESSIONS.pop(self.thread_id, None)
			# await interaction.response.send_message(getlang(LANGUAGE_DICT, "RoomClosedNoPlayers"), ephemeral=True)
			
			thread = interaction.channel
			if isinstance(thread, discord.Thread):
				await thread.send(getlang(LANGUAGE_DICT, "RoomClosedNoPlayers"))
				await thread.delete()
			return

		old_host_id = session.get("host_id")
		new_host_id = old_host_id
		if user_id == old_host_id:
			new_host_id = next(iter(session["players"].keys()))
			session["host_id"] = new_host_id

		embed = _render_room_embed(session)
		message = interaction.message
		if message:
			await message.edit(embed=embed, view=self)

		if user_id == old_host_id:
			# await interaction.response.send_message(
			# 	getlang(LANGUAGE_DICT, "RoomHostTransferred").format(old=f"<@{old_host_id}>", new=f"<@{new_host_id}>"),
			# 	ephemeral=True,
			# )
			thread = interaction.channel
			if isinstance(thread, discord.Thread):
				await thread.send(getlang(LANGUAGE_DICT, "RoomHostTransferred").format(old=f"<@{old_host_id}>", new=f"<@{new_host_id}>"))
		else:
			await interaction.response.send_message(getlang(LANGUAGE_DICT, "RoomLeaveSuccess").format(user=interaction.user.mention), ephemeral=True)

@bot.event
async def on_ready():
	logger.info("Bot is ready.")
	logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_disconnect():
	logger.warning("Discord connection lost. Attempting to reconnect...")


@bot.event
async def on_resumed():
	logger.info("Discord connection resumed.")


@bot.slash_command(name="ping", description=getlang(LANGUAGE_DICT, "CheckBotLatencycmd"))
async def ping(ctx: discord.ApplicationContext):
	try:
		if not ctx.response.is_done():
			await ctx.defer()

		if not WHAT_IS_THIS_SETTING:
			latency = round(bot.latency * 1000)
			embed = discord.Embed(title=getlang(LANGUAGE_DICT, "CheckBotLatencyTitle"), description=getlang(LANGUAGE_DICT, "CheckBotLatencyDescription").format(latency=latency), color=discord.Color.blue())
			await ctx.followup.send(embed=embed)
		else:
			embed = f"{random.choice(WHAT_IS_THIS_LIST2)}\n{random.choice(WHAT_IS_THIS_LIST)}\n-# {round(bot.latency * 1000)}ms"
			await ctx.followup.send(embed)
	except Exception as e:
		logger.exception(f"ping command failed: error={e}")
	
@bot.slash_command(name="echo", description="입력한 메시지를 그대로 반환하는 슬래시 명령어")
async def echo(ctx: discord.ApplicationContext, message: str):
	embed = discord.Embed(title="🔊 에코", description=f"# {message}", color=discord.Color.purple())
	await ctx.respond(embed=embed) # Not Used, Just for testing


def room_opts_autocomplete(ctx: discord.AutocompleteContext):
	partial = str(ctx.value or "").strip().lower()
	choices: list[discord.OptionChoice] = []

	for option_value, option_label in get_room_option_catalog(LANGUAGE_DICT):
		label_lower = option_label.lower()
		if partial and (partial not in option_value and partial not in label_lower):
			continue

		choices.append(discord.OptionChoice(name=option_label, value=option_value))

		if len(choices) >= 25:
			break

	return choices
	


@bot.slash_command(name="room-make", description=getlang(LANGUAGE_DICT, "RoomMakecmd"))
async def start_game(
	ctx: discord.ApplicationContext,
	room_name: str,
	# password: str = None, # 비밀번호 인증을 어케 하지
	mode: str,
	limit: int = 8,
	round: int = 5,
	time: int = 60,
	):
	"""
	게임시작 -> 
	입력을 토대로 방(스레드)생성 ->
	입장처리...? 스레드에 봇이 먼저 메시지를 보낸후 버튼을 생성 ->
	게임 진행 로직 ->
	게임 종료 및 결과 처리
	"""
	try:
		if not ctx.response.is_done():
			await ctx.defer(ephemeral=True)

		if not ctx.guild or not hasattr(ctx.channel, "create_thread"):
			await ctx.followup.send(getlang(LANGUAGE_DICT, "RoomMakeChannelNotSupported"), ephemeral=True)
			return

		safe_limit = max(2, min(limit, 32))
		safe_round = max(1, min(round, 30))
		safe_time = max(10, min(time, 300))

		starter_message = await ctx.channel.send(
			getlang(LANGUAGE_DICT, "RoomThreadStarterMessage").format(room=room_name)
		)
		thread = await starter_message.create_thread(
			name=f"{room_name}",
			auto_archive_duration=60,
		)

		session = {
			"thread_id": thread.id,
			"name": room_name,
			"host_id": ctx.user.id,
			"mode": mode,
			"limit": safe_limit,
			"round": safe_round,
			"time": safe_time,
			"options": [],
			"room_message_id": None,
			"players": {ctx.user.id: ctx.user.display_name},
		}
		ROOM_SESSIONS[thread.id] = session

		view = RoomJoinView(thread.id)
		embed = _render_room_embed(session)
		room_message = await thread.send(embed=embed, view=view)
		session["room_message_id"] = room_message.id
		await thread.add_user(ctx.user)

		await ctx.followup.send(
			getlang(LANGUAGE_DICT, "RoomMakeThreadCreated").format(thread=thread.mention),
			ephemeral=True,
		)
		
		
	except Exception as e:
		logger.exception(f"start_game command failed: error={e}")


@bot.slash_command(name="room-set", description=getlang(LANGUAGE_DICT, "RoomSetcmd"))
async def room_set_command(
	ctx: discord.ApplicationContext,
	target: str = discord.Option(choices=["opts", "set"], description=getlang(LANGUAGE_DICT, "RoomSetTargetDescription")),
	action: str = discord.Option(choices=["add", "del", "name"], description=getlang(LANGUAGE_DICT, "RoomSetActionDescription")),
	opts: str = discord.Option(default="", description=getlang(LANGUAGE_DICT, "RoomOptionSelectorDescription"), autocomplete=room_opts_autocomplete, required=False),
	value: str = discord.Option(default="", description=getlang(LANGUAGE_DICT, "RoomSetValueDescription"), required=False),
):
	try:
		if not ctx.response.is_done():
			await ctx.defer(ephemeral=True)

		channel = ctx.channel
		if not isinstance(channel, discord.Thread):
			await ctx.followup.send(getlang(LANGUAGE_DICT, "RoomSetThreadOnly"), ephemeral=True)
			return

		session = ROOM_SESSIONS.get(channel.id)
		if not session:
			await ctx.followup.send(getlang(LANGUAGE_DICT, "RoomSessionClosed"), ephemeral=True)
			return

		if ctx.user.id != session.get("host_id"):
			await ctx.followup.send(getlang(LANGUAGE_DICT, "RoomSetHostOnly"), ephemeral=True)
			return

		if target == "opts":
			if action not in ("add", "del"):
				await ctx.followup.send(getlang(LANGUAGE_DICT, "RoomSetInvalidAction"), ephemeral=True)
				return

			normalized_opt = str(opts or "").strip().lower()
			if not normalized_opt:
				await ctx.followup.send(getlang(LANGUAGE_DICT, "RoomOptionEmptyInput"), ephemeral=True)
				return

			if normalized_opt not in ROOM_OPTION_VALUES:
				await ctx.followup.send(
					getlang(LANGUAGE_DICT, "RoomOptionInvalid").format(opts=normalized_opt),
					ephemeral=True,
				)
				return

			current_options = list(session.get("options", []))
			if action == "add":
				if normalized_opt in current_options:
					await ctx.followup.send(getlang(LANGUAGE_DICT, "RoomSetNoChange"), ephemeral=True)
					return
				current_options.append(normalized_opt)
				action_text = getlang(LANGUAGE_DICT, "RoomSetActionAdd")
				updated = normalized_opt
			else:
				if normalized_opt not in current_options:
					await ctx.followup.send(getlang(LANGUAGE_DICT, "RoomSetNoChange"), ephemeral=True)
					return
				current_options = [opt for opt in current_options if opt != normalized_opt]
				action_text = getlang(LANGUAGE_DICT, "RoomSetActionDel")
				updated = normalized_opt

			session["options"] = current_options
			success_msg = getlang(LANGUAGE_DICT, "RoomSetSuccess").format(action=action_text, opts=updated)
		elif target == "set":
			if action != "name":
				await ctx.followup.send(getlang(LANGUAGE_DICT, "RoomSetInvalidAction"), ephemeral=True)
				return

			new_name = str(value or "").strip()
			if not new_name:
				await ctx.followup.send(getlang(LANGUAGE_DICT, "RoomSetNameEmpty"), ephemeral=True)
				return

			session["name"] = new_name
			try:
				await channel.edit(name=new_name)
			except Exception:
				pass

			success_msg = getlang(LANGUAGE_DICT, "RoomSetNameUpdated").format(name=new_name)
		else:
			await ctx.followup.send(getlang(LANGUAGE_DICT, "RoomSetUnsupportedTarget"), ephemeral=True)
			return

		embed = _render_room_embed(session)
		room_message_id = session.get("room_message_id")
		if not room_message_id:
			await ctx.followup.send(getlang(LANGUAGE_DICT, "RoomStateMessageMissing"), ephemeral=True)
			return

		try:
			room_message = await channel.fetch_message(room_message_id)
		except Exception:
			await ctx.followup.send(getlang(LANGUAGE_DICT, "RoomStateMessageMissing"), ephemeral=True)
			return

		await room_message.edit(embed=embed)
		await ctx.followup.send(
			success_msg,
			ephemeral=True,
		)
	except Exception as e:
		logger.exception(f"room_set_command failed: error={e}")
		await ctx.followup.send(getlang(LANGUAGE_DICT, "HasError").format(error=str(e)), ephemeral=True)
	
@bot.slash_command(name="submit", description=getlang(LANGUAGE_DICT, "Submitcmd"))
async def input_command(ctx: discord.ApplicationContext, user_input: str):
	try:
		if not ctx.response.is_done():
			await ctx.defer()
		embed = discord.Embed(title=getlang(LANGUAGE_DICT, "SubmitTitle"), description=getlang(LANGUAGE_DICT, "SubmitDescription").format(message=user_input), color=discord.Color.yellow())
		await ctx.followup.send(embed=embed)
	except Exception as e:
		logger.exception(f"submit command failed: error={e}")


@bot.slash_command(name="search", description=getlang(LANGUAGE_DICT, "Searchcmd"))
async def search_command(
	ctx: discord.ApplicationContext,
	query: str,
	is_regex: bool = False,
	theme: str = "",
	limit: int = SEARCH_LIMIT
):
	response_sent = False
	try:
		if not ctx.response.is_done():
			await ctx.defer()

		if is_regex and not isRegexSafe(query):
			embed = discord.Embed(
				title=getlang(LANGUAGE_DICT, "HasErrorTitle"),
				description=getlang(LANGUAGE_DICT, "RegexUnsafe"),
				color=discord.Color.red(),
			)
			await ctx.followup.send(embed=embed)
			response_sent = True
			return

		results = SearchDB(
			"kkutu_ko",
			query,
			is_regex=is_regex,
			db_path=DB_PATH,
			dblimit=limit,
			theme=theme if theme else None,
			use_pgsql=USE_PGSQL,
			pgsql_config=PGSQL_CONFIG,
		)
		
		if results:
			result_text = listwords([word['_id'] for word in results])
			embed = discord.Embed(
				title=getlang(LANGUAGE_DICT, "SearchTitle").format(query=query),
				description=getlang(LANGUAGE_DICT, "SearchDescription").format(results=result_text),
				color=discord.Color.blue(),
				timestamp=datetime.datetime.now(),
			)
			footer_text = getlang(LANGUAGE_DICT, "SearchFooter").format(total=len(results))
			if theme:
				footer_text += " " + getlang(LANGUAGE_DICT, "SearchthemeFooter").format(theme=theme)
			embed.set_footer(text=footer_text)
			await ctx.followup.send(embed=embed)
			response_sent = True
		else:
			embed = discord.Embed(
				title=getlang(LANGUAGE_DICT, "SearchTitle").format(query=query),
				description=getlang(LANGUAGE_DICT, "SearchNotfound"),
				color=discord.Color.red(),
				timestamp=datetime.datetime.now(),
			)
			footer_text = getlang(LANGUAGE_DICT, "SearchFooter").format(total=0)
			if theme:
				footer_text += " " + getlang(LANGUAGE_DICT, "SearchthemeFooter").format(theme=theme)
			embed.set_footer(text=footer_text)
			await ctx.followup.send(embed=embed)
			response_sent = True
	except Exception as e:
		logger.exception(f"search_command failed: query={query}, error={e}")
		if not response_sent:
			embed = discord.Embed(title=getlang(LANGUAGE_DICT, "HasErrorTitle"), description=getlang(LANGUAGE_DICT, "HasError").format(error=str(e)), color=discord.Color.red())
			try:
				await ctx.followup.send(embed=embed)
			except Exception as followup_error:
				logger.exception(f"failed to send search error followup: {followup_error}")


@bot.slash_command(name="char", description=getlang(LANGUAGE_DICT, "CharSearchcmd"))
async def search_char_command(
	ctx: discord.ApplicationContext,
	char: str,
	position: str = discord.Option(default="start", choices=["start", "end"])
):
	try:
		if not ctx.response.is_done():
			await ctx.defer()

		if len(char) != 1 or not VALID_WORD_CHARS.fullmatch(char):
			embed = discord.Embed(
				title=getlang(LANGUAGE_DICT, "HasErrorTitle"),
				description=getlang(LANGUAGE_DICT, "CharSearchInvalidChar"),
				color=discord.Color.red(),
			)
			await ctx.followup.send(embed=embed)
			return

		lang = detect_language(char)
		table = f"kkutu_{lang}"
		results = SearchByChar(
			table=table,
			char=char,
			position=position,
			dblimit=SEARCH_LIMIT,
			db_path=DB_PATH,
			use_pgsql=USE_PGSQL,
			pgsql_config=PGSQL_CONFIG,
		)

		if not results:
			pos_text = "시작하는" if position == "start" else "끝나는"
			embed = discord.Embed(
				title=getlang(LANGUAGE_DICT, "CharSearchTitle").format(char=char, pos_text=pos_text),
				description=getlang(LANGUAGE_DICT, "CharSearchNotfound").format(char=char, pos_text=pos_text),
				color=discord.Color.red(),
				timestamp=datetime.datetime.now(),
			)
			await ctx.followup.send(embed=embed)
			return

		lines = [f"{i}. **{w.get('_id', '')}** ({len(str(w.get('_id', '')))}자)" for i, w in enumerate(results, start=1)]
		pos_text = "시작하는" if position == "start" else "끝나는"
		embed = discord.Embed(
			title=getlang(LANGUAGE_DICT, "CharSearchTitle").format(char=char, pos_text=pos_text),
			description="\n".join(lines),
			color=discord.Color(0x9B59B6),
			timestamp=datetime.datetime.now(),
		)
		embed.set_footer(text=getlang(LANGUAGE_DICT, "CharSearchFooter").format(total=len(results)))
		await ctx.followup.send(embed=embed)
	except Exception as e:
		logger.exception(f"search_char_command failed: char={char}, error={e}")
		embed = discord.Embed(title=getlang(LANGUAGE_DICT, "HasErrorTitle"), description=getlang(LANGUAGE_DICT, "HasError").format(error=str(e)), color=discord.Color.red())
		await ctx.followup.send(embed=embed)


@bot.slash_command(name="mission", description=getlang(LANGUAGE_DICT, "MissionSearchcmd"))
async def search_mission_command(
	ctx: discord.ApplicationContext,
	mission: str,
	topic: str = "",
	target_char: str = "",
	position: str = discord.Option(default="start", choices=["start", "end"]),
):
	try:
		if not ctx.response.is_done():
			await ctx.defer()

		if len(mission) != 1 or not VALID_WORD_CHARS.fullmatch(mission):
			embed = discord.Embed(title=getlang(LANGUAGE_DICT, "HasErrorTitle"), description=getlang(LANGUAGE_DICT, "MissionInvalidMissionChar"), color=discord.Color.red())
			await ctx.followup.send(embed=embed)
			return

		if target_char and (len(target_char) != 1 or not VALID_WORD_CHARS.fullmatch(target_char)):
			embed = discord.Embed(title=getlang(LANGUAGE_DICT, "HasErrorTitle"), description=getlang(LANGUAGE_DICT, "MissionInvalidTargetChar"), color=discord.Color.red())
			await ctx.followup.send(embed=embed)
			return

		results = SearchMissionWords(
			table="kkutu_ko",
			mission_char=mission,
			topic=topic if topic else None,
			target_char=target_char if target_char else None,
			position=position,
			dblimit=SEARCH_LIMIT,
			db_path=DB_PATH,
			use_pgsql=USE_PGSQL,
			pgsql_config=PGSQL_CONFIG,
		)

		if not results:
			desc_parts = [getlang(LANGUAGE_DICT, "MissionNotfoundBase").format(mission=mission)]
			if target_char:
				pos_text = "끝나는" if position == "end" else "시작하는"
				desc_parts.append(getlang(LANGUAGE_DICT, "MissionNotfoundTarget").format(target=target_char, pos_text=pos_text))
			if topic:
				desc_parts.append(getlang(LANGUAGE_DICT, "MissionNotfoundTopic").format(topic=topic))
			embed = discord.Embed(
				title=getlang(LANGUAGE_DICT, "MissionSearchTitle").format(mission=mission),
				description=" / ".join(desc_parts),
				color=discord.Color.red(),
				timestamp=datetime.datetime.now(),
			)
			await ctx.followup.send(embed=embed)
			return

		lines = []
		for i, w in enumerate(results, start=1):
			wid = str(w.get("_id", ""))
			mission_count = count_char_occurrences(wid, mission)
			lines.append(
				f"{i}. {format_word(wid, w.get('flag'), w.get('type'))} ({len(wid)}자, 미션 {mission_count}개)"
			)

		title_filters = []
		if target_char:
			title_filters.append(getlang(LANGUAGE_DICT, "MissionFilterTarget").format(pos="끝" if position == "end" else "시작", target=target_char))
		if topic:
			title_filters.append(getlang(LANGUAGE_DICT, "MissionFilterTopic").format(topic=topic))

		description = "\n".join(lines)
		if title_filters:
			description = " | ".join(title_filters) + "\n\n" + description

		embed = discord.Embed(
			title=getlang(LANGUAGE_DICT, "MissionSearchTitle").format(mission=mission),
			description=description,
			color=discord.Color(0xE91E63),
			timestamp=datetime.datetime.now(),
		)
		embed.set_footer(text=getlang(LANGUAGE_DICT, "MissionSearchFooter").format(total=len(results)))
		await ctx.followup.send(embed=embed)
	except Exception as e:
		logger.exception(f"search_mission_command failed: mission={mission}, error={e}")
		embed = discord.Embed(title=getlang(LANGUAGE_DICT, "HasErrorTitle"), description=getlang(LANGUAGE_DICT, "HasError").format(error=str(e)), color=discord.Color.red())
		await ctx.followup.send(embed=embed)


@bot.slash_command(name="random", description=getlang(LANGUAGE_DICT, "RandomSearchcmd"))
async def random_command(ctx: discord.ApplicationContext, count: int = 1):
	try:
		if not ctx.response.is_done():
			await ctx.defer()

		safe_count = max(1, min(count, MAX_RANDOM_COUNT))
		results = SearchRandomWords(
			table="kkutu_ko",
			count=safe_count,
			db_path=DB_PATH,
			use_pgsql=USE_PGSQL,
			pgsql_config=PGSQL_CONFIG,
		)

		if not results:
			embed = discord.Embed(
				title=getlang(LANGUAGE_DICT, "RandomSearchTitle").format(total=0),
				description=getlang(LANGUAGE_DICT, "RandomSearchNotfound"),
				color=discord.Color.red(),
				timestamp=datetime.datetime.now(),
			)
			await ctx.followup.send(embed=embed)
			return

		lines = []
		for i, w in enumerate(results, start=1):
			meaning = parse_meaning(w.get("mean"))
			short_meaning = meaning.split("\n")[0][:80] if meaning else getlang(LANGUAGE_DICT, "MeanSearchmeanNotfound")
			lines.append(f"{i}. **{w.get('_id', '')}** - {short_meaning}")

		embed = discord.Embed(
			title=getlang(LANGUAGE_DICT, "RandomSearchTitle").format(total=len(results)),
			description="\n".join(lines),
			color=discord.Color(0xF39C12),
			timestamp=datetime.datetime.now(),
		)
		await ctx.followup.send(embed=embed)
	except Exception as e:
		logger.exception(f"random_command failed: error={e}")
		embed = discord.Embed(title=getlang(LANGUAGE_DICT, "HasErrorTitle"), description=getlang(LANGUAGE_DICT, "HasError").format(error=str(e)), color=discord.Color.red())
		await ctx.followup.send(embed=embed)

@bot.slash_command(name="mean", description=getlang(LANGUAGE_DICT, "MeanSearchcmd"))
async def search_mean_command(ctx: discord.ApplicationContext, query: str):
	respones_sent = False
	try:
		if not ctx.response.is_done():
			await ctx.defer()
		result = Getmean(
			"kkutu_ko",
			query,
			db_path=DB_PATH,
			use_pgsql=USE_PGSQL,
			pgsql_config=PGSQL_CONFIG,
		)
		if result:
			result_text = format_mean_text(
				result.get("mean"),
				result.get("theme"),
				getlang(LANGUAGE_DICT, "MeanSearchmeanNotfound"),
			)
			fallback_text = getlang(LANGUAGE_DICT, "MeanSearchfieldNotfound")
			type_name_map = LANGUAGE_DICT.get("MeanTypeNameMap", {})
			flag_name_map = LANGUAGE_DICT.get("MeanFlagNameMap", {})
			type_text = format_type_text(result.get("type"), type_name_map, fallback_text)
			theme_text = format_theme_text(result.get("theme"), fallback_text)
			flag_text = format_flag_text(result.get("flag"), flag_name_map, fallback_text)
			embed = discord.Embed(
				title=getlang(LANGUAGE_DICT, "MeanSearchTitle").format(query=query),
				description=result_text,
				color=discord.Color.yellow(),
				timestamp=datetime.datetime.now(),
			)
			embed.add_field(name=getlang(LANGUAGE_DICT, "MeanSearchtype").format(type=type_text), value="\u200b", inline=True)
			embed.add_field(name=getlang(LANGUAGE_DICT, "MeanSearchtheme").format(theme=theme_text), value="\u200b", inline=True)
			embed.add_field(name=getlang(LANGUAGE_DICT, "MeanSearchflag").format(flag=flag_text), value="\u200b", inline=True)
			await ctx.followup.send(embed=embed)
			respones_sent = True
		else:
			embed = discord.Embed(
				title=getlang(LANGUAGE_DICT, "MeanSearchTitle").format(query=query),
				description=getlang(LANGUAGE_DICT, "MeanSearchmeanNotfound"),
				color=discord.Color.red(),
				timestamp=datetime.datetime.now(),
			)
			await ctx.followup.send(embed=embed)
			respones_sent = True
	except Exception as e:
		logger.exception(f"search_command failed: query={query}, error={e}")
		if not respones_sent:
			embed = discord.Embed(title=getlang(LANGUAGE_DICT, "HasErrorTitle"), description=getlang(LANGUAGE_DICT, "HasError").format(error=str(e)), color=discord.Color.red())
			try:
				await ctx.followup.send(embed=embed)
			except Exception as followup_error:
				logger.exception(f"failed to send search error followup: {followup_error}")

@bot.slash_command(name="theme", description=getlang(LANGUAGE_DICT, "ThemeSearchcmd"))
async def search_theme_command(ctx: discord.ApplicationContext, theme: str):
	try:
		if not ctx.response.is_done():
			await ctx.defer()
		results = SearchDB(
			"kkutu_ko",
			"",
			db_path=DB_PATH,
			dblimit=SEARCH_LIMIT,
			theme=theme,
			use_pgsql=USE_PGSQL,
			pgsql_config=PGSQL_CONFIG,
		)
		if results:
			sorted_results = sorted(
				results,
				key=lambda w: len(str(w.get("_id", ""))),
				reverse=True,
			)
			result_lines = [
				f"{i}. **{word.get('_id', '')}** ({len(str(word.get('_id', '')))}자)"
				for i, word in enumerate(sorted_results, start=1)
			]
			embed = discord.Embed(
				title=getlang(LANGUAGE_DICT, "ThemeSearchTitle").format(theme=theme),
				description="\n".join(result_lines),
				color=discord.Color.green(),
				timestamp=datetime.datetime.now(),
			)
			embed.set_footer(text=getlang(LANGUAGE_DICT, "ThemeSearchFooter").format(total=len(sorted_results)))
			await ctx.followup.send(embed=embed)
		else:
			embed = discord.Embed(
				title=getlang(LANGUAGE_DICT, "ThemeSearchTitle").format(theme=theme),
				description=getlang(LANGUAGE_DICT, "ThemeSearchNotfound").format(theme=theme),
				color=discord.Color.red(),
				timestamp=datetime.datetime.now(),
			)
			await ctx.followup.send(embed=embed)
	except Exception as e:
		logger.exception(f"search_theme_command failed: theme={theme}, error={e}")
		embed = discord.Embed(title=getlang(LANGUAGE_DICT, "HasErrorTitle"), description=getlang(LANGUAGE_DICT, "HasError").format(error=str(e)), color=discord.Color.red())
		try:
			await ctx.followup.send(embed=embed)
		except Exception as followup_error:
			logger.exception(f"failed to send theme search error followup: {followup_error}")

@bot.slash_command(name="help", description=getlang(LANGUAGE_DICT, "Helpcmd")) # 나중에
async def help_command(ctx: discord.ApplicationContext):
	embed = discord.Embed(title=getlang(LANGUAGE_DICT, "HelpTitle"), description=getlang(LANGUAGE_DICT, "HelpDescription"), color=discord.Color.green())
	embed.add_field(name="/ping", value=getlang(LANGUAGE_DICT, "CheckBotLatencycmd"), inline=False)
	# embed.add_field(name="/echo [message]", value="입력한 메시지를 그대로 반환하는 명령어입니다.", inline=False)
	embed.add_field(name="/room-make [room_name] [mode] [limit] [round] [time]", value=getlang(LANGUAGE_DICT, "RoomMakecmd"), inline=False)
	embed.add_field(name="/room-set [target] [action] [opts] [value]", value=getlang(LANGUAGE_DICT, "RoomSetcmd"), inline=False)
	embed.add_field(name="/submit [message]", value=getlang(LANGUAGE_DICT, "Submitcmd"), inline=False)
	embed.add_field(name="/search [query] [is_regex] [theme] [limit]", value=getlang(LANGUAGE_DICT, "Searchcmd"), inline=False)
	embed.add_field(name="/theme [theme]", value=getlang(LANGUAGE_DICT, "ThemeSearchcmd"), inline=False)
	embed.add_field(name="/char [char] [position]", value=getlang(LANGUAGE_DICT, "CharSearchcmd"), inline=False)
	embed.add_field(name="/mission [mission] [topic] [target_char] [position]", value=getlang(LANGUAGE_DICT, "MissionSearchcmd"), inline=False)
	embed.add_field(name="/random [count]", value=getlang(LANGUAGE_DICT, "RandomSearchcmd"), inline=False)
	embed.add_field(name="/mean [query]", value=getlang(LANGUAGE_DICT, "MeanSearchcmd"), inline=False)
	embed.set_footer(text="By minjun1177・<https://github.com/minjun1177/KKuTu-on-Discord-real>")
	await ctx.respond(embed=embed)

def main():
	CheckDB(USE_PGSQL, PGSQL_CONFIG, DB_PATH)

	try:
		with open("settings.json", "r", encoding="utf-8") as f:
			settings = json.load(f)
	except (FileNotFoundError, json.JSONDecodeError) as e:
		logger.error(f"Failed to load settings.json: {e}")
		settings = {}

	token = settings.get("DISCORD_BOT_TOKEN")

	if not token:
		raise RuntimeError("Please set the DISCORD_BOT_TOKEN provide it in settings.json")

	bot.run(token, reconnect=True)


if __name__ == "__main__":
	main()
