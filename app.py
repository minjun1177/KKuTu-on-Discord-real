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

from util.db import SearchDB, Getmean
from util.meanutil import format_mean_text, format_theme_text, format_type_text, format_flag_text
from util.langutil import check_language_keys, getlang

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
with open("settings.json", "r", encoding="utf-8") as f:
	SETTINGS = json.load(f)
	
DB_PATH = SETTINGS.get("DB_PATH", "db.json")
LANGUAGE_PATH = SETTINGS.get("LANGUAGE_PATH", "ko_kr.json")
SEARCH_LIMIT = SETTINGS.get("SEARCH_RESULT_LIMIT", 20)
PGSQL_CONFIG = SETTINGS.get("PGSQL_CONFIG", {})
USE_PGSQL = bool(PGSQL_CONFIG.get("USE_PGSQL", False))
WHAT_IS_THIS_SETTING = SETTINGS.get("WHAT_IS_THIS_SETTING", False)
WHAT_IS_THIS_LIST = SETTINGS.get("WHAT_IS_THIS_LIST", [])
WHAT_IS_THIS_LIST2 = SETTINGS.get("WHAT_IS_THIS_LIST2", [])

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

@bot.event
async def on_ready():
	logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")


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
	


@bot.slash_command(name="game_start", description=getlang(LANGUAGE_DICT, "GameStartcmd"))
async def start_game(ctx: discord.ApplicationContext):
	try:
		if not ctx.response.is_done():
			await ctx.defer()
		embed = discord.Embed(title=getlang(LANGUAGE_DICT, "GameStartTitle"), description=getlang(LANGUAGE_DICT, "GameStartDescription"), color=discord.Color.orange())
		await ctx.followup.send(embed=embed)
	except Exception as e:
		logger.exception(f"start_game command failed: error={e}")
	
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

@bot.slash_command(name="mean", description=getlang(LANGUAGE_DICT, "ThemeSearchcmd"))
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
				getlang(LANGUAGE_DICT, "ThemeSearchmeanNotfound"),
			)
			fallback_text = getlang(LANGUAGE_DICT, "ThemeSearchfieldNotfound")
			type_name_map = LANGUAGE_DICT.get("ThemeTypeNameMap", {})
			flag_name_map = LANGUAGE_DICT.get("ThemeFlagNameMap", {})
			type_text = format_type_text(result.get("type"), type_name_map, fallback_text)
			theme_text = format_theme_text(result.get("theme"), fallback_text)
			flag_text = format_flag_text(result.get("flag"), flag_name_map, fallback_text)
			embed = discord.Embed(
				title=getlang(LANGUAGE_DICT, "ThemeSearchTitle").format(query=query),
				description=result_text,
				color=discord.Color.yellow(),
				timestamp=datetime.datetime.now(),
			)
			embed.add_field(name=getlang(LANGUAGE_DICT, "ThemeSearchtype").format(type=type_text), value="\u200b", inline=True)
			embed.add_field(name=getlang(LANGUAGE_DICT, "ThemeSearchtheme").format(theme=theme_text), value="\u200b", inline=True)
			embed.add_field(name=getlang(LANGUAGE_DICT, "ThemeSearchflag").format(flag=flag_text), value="\u200b", inline=True)
			await ctx.followup.send(embed=embed)
			respones_sent = True
		else:
			embed = discord.Embed(
				title=getlang(LANGUAGE_DICT, "ThemeSearchTitle").format(query=query),
				description=getlang(LANGUAGE_DICT, "ThemeSearchmeanNotfound"),
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

@bot.slash_command(name="help", description=getlang(LANGUAGE_DICT, "Helpcmd")) # 나중에
async def help_command(ctx: discord.ApplicationContext):
	embed = discord.Embed(title=getlang(LANGUAGE_DICT, "HelpTitle"), description=getlang(LANGUAGE_DICT, "HelpDescription"), color=discord.Color.green())
	embed.add_field(name="/ping", value=getlang(LANGUAGE_DICT, "CheckBotLatencycmd"), inline=False)
	# embed.add_field(name="/echo [message]", value="입력한 메시지를 그대로 반환하는 명령어입니다.", inline=False)
	embed.add_field(name="/game_start", value=getlang(LANGUAGE_DICT, "GameStartcmd"), inline=False)
	embed.add_field(name="/submit [message]", value=getlang(LANGUAGE_DICT, "Submitcmd"), inline=False)
	embed.add_field(name="/search [query] [is_regex] [theme] [limit]", value=getlang(LANGUAGE_DICT, "Searchcmd"), inline=False)
	embed.add_field(name="/mean [query]", value=getlang(LANGUAGE_DICT, "ThemeSearchcmd"), inline=False)
	embed.set_footer(text="By minjun1177・<https://github.com/minjun1177/KKuTu-on-Discord-real>")
	await ctx.respond(embed=embed)

def main():
	with open("settings.json", "r", encoding="utf-8") as f:
		settings = json.load(f)

	token = settings.get("DISCORD_BOT_TOKEN")

	if not token:
		raise RuntimeError("DISCORD_BOT_TOKEN을 settings.json에 설정해주세요.")

	bot.run(token)


if __name__ == "__main__":
	main()
