'''
KKuTu on Discord - A bot for the KKuTu game

TODO:
- [ ] 게임 진행 로직 구현
- - 기타 게임 유틸리티
- - - [ ] 단어 검색 기능
- [ ] 게임 상태 관리
- [ ] 사용자 인터랙션 처리
- [ ] 에러 핸들링 및 예외 처리
- [ ] 추가 명령어 및 기능 구현
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

from util.db import SearchDB

import discord
from discord.ext import commands


intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)

global SETTINGS, DB_PATH, LANGUAGE_PATH, SEARCH_LIMIT, WHAT_IS_THIS_SETTING, WHAT_IS_THIS_LIST, WHAT_IS_THIS_LIST2
with open("settings.json", "r", encoding="utf-8") as f:
	SETTINGS = json.load(f)
	
DB_PATH = SETTINGS.get("DB_PATH", "db.json")
LANGUAGE_PATH = SETTINGS.get("LANGUAGE_PATH", "ko_kr.json")
SEARCH_LIMIT = SETTINGS.get("SEARCH_RESULT_LIMIT", 20)
WHAT_IS_THIS_SETTING = SETTINGS.get("WHAT_IS_THIS_SETTING", False)
WHAT_IS_THIS_LIST = SETTINGS.get("WHAT_IS_THIS_LIST", [])
WHAT_IS_THIS_LIST2 = SETTINGS.get("WHAT_IS_THIS_LIST2", [])

def listwords(word: list):
	# add 1 to 20 on word but cut from 20
	# example : ["asdf", "asdfasdf"]
	# result : "1. asdf\n2. asdfasdf\n"
	result = ""
	for i, w in enumerate(word[:SEARCH_LIMIT + 1], start=1):
		result += f"{i}. {w}\n"
	return result

@bot.event
async def on_ready():
	print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.slash_command(name="ping", description="봇 응답 속도 확인")
async def ping(ctx: discord.ApplicationContext):
	if not WHAT_IS_THIS_SETTING:
		await ctx.respond(f"🏓 Pong!\n응답 시간: **{round(bot.latency * 1000)}ms**\n")
	else:
		embed = f"{random.choice(WHAT_IS_THIS_LIST2)}\n{random.choice(WHAT_IS_THIS_LIST)}\n-# {round(bot.latency * 1000)}ms"
		await ctx.respond(embed)


@bot.slash_command(name="hello", description="인사 예시 슬래시 명령어")
async def hello(ctx: discord.ApplicationContext):
	embed = discord.Embed(title="👋 인사", description=f"안녕하세요, {ctx.author.mention}님!", color=discord.Color.green())
	await ctx.respond(embed=embed)
	
@bot.slash_command(name="echo", description="입력한 메시지를 그대로 반환하는 슬래시 명령어")
async def echo(ctx: discord.ApplicationContext, message: str):
	embed = discord.Embed(title="🔊 에코", description=message, color=discord.Color.purple())
	await ctx.respond(embed=embed)
	


@bot.slash_command(name="game_start", description="게임 시작 명령어")
async def start_game(ctx: discord.ApplicationContext):
	embed = discord.Embed(title="🎮 게임 시작", description="게임을 시작하시겠습니까?", color=discord.Color.orange())
	await ctx.respond(embed=embed)
	
@bot.slash_command(name="submit", description="입력 명령어")
async def input_command(ctx: discord.ApplicationContext, user_input: str):
	embed = discord.Embed(title="📝 입력", description=f"**입력 내용:**\n{user_input}", color=discord.Color.yellow())
	await ctx.respond(embed=embed)


@bot.slash_command(name="search", description="단어 검색 명령어 (정규식 지원)")
async def search_command(
	ctx: discord.ApplicationContext,
	query: str,
	is_regex: bool = False,
	theme: str = "",
	limit: int = SEARCH_LIMIT
):
	try:
		results = SearchDB(
			"kkutu_ko",
			query,
			is_regex=is_regex,
			db_path=DB_PATH,
			dblimit=limit,
			theme=theme if theme else None,
		)
		
		if results:
			result_text = listwords([word['_id'] for word in results])
			embed = discord.Embed(title=f"🔍 \"{query}\" 검색 결과", description=f"\n{result_text}", color=discord.Color.blue(), timestamp=datetime.datetime.now())
			footer_text = f"총 {len(results)}개 결과"
			if theme:
				footer_text += f" | theme: {theme}"
			embed.set_footer(text=footer_text)
			await ctx.respond(embed=embed)
		else:
			embed = discord.Embed(title=f"🔍 \"{query}\" 검색 결과", description="검색 결과가 없습니다.", color=discord.Color.red(), timestamp=datetime.datetime.now())
			footer_text = "총 0개 결과"
			# if theme:
			# 	footer_text += f" | theme: {theme}"
			embed.set_footer(text=footer_text)
			await ctx.respond(embed=embed)
	except Exception as e:
		embed = discord.Embed(title="❌ 오류", description=f"오류 발생: {str(e)}", color=discord.Color.red())
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
