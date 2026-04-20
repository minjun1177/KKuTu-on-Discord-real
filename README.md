# KKuTu-on-Discord-real

- Made by [minjun1177](https://github.com/minjun1177)
- Special thanks to:
    - Idea by [JJoriping](https://github.com/JJoriping), [Original repository](https://github.com/JJoriping/KKuTu)
    - Beta tester: discord(siwoohan)
    - You to have interested in this repository :)

## Languages
- [한국어](#한국어)
- [English](#english)

## 한국어
> 디스코드로 놀자! KKuTu on Discord

이 프로젝트는 [끄투](https://github.com/JJoriping/KKuTu)에서 영감을 받아 디스코드 봇으로 재해석한 저장소입니다.

### 설치 방법

#### Linux
1. 저장소를 클론하거나 다운로드합니다.
1. [Python](https://python.org/)을 설치합니다.
     - Python 3.13.5에서 동작을 확인했습니다.
     - 설치 시 pip가 함께 설치되어야 합니다.
1. 의존성을 설치합니다.
     - `pip install -r requirements.txt`
1. (선택) [SQL 파일](https://github.com/JJoriping/KKuTu/blob/master/db.sql)을 PostgreSQL 데이터베이스에 입력합니다.
     - 예시: `sudo -u postgres psql --quiet main < ./db.sql`
1. 봇을 실행합니다.
     - `./start-bot.sh`
     - 종료는 `./stop-bot.sh` 사용을 권장합니다.

#### Windows
1. 저장소를 클론하거나 다운로드합니다.
1. [Python](https://python.org/)을 설치합니다.
     - Python 3.13.5에서 동작을 확인했습니다.
     - 설치 시 Add Python to PATH 옵션을 활성화하는 것을 권장합니다.
1. PowerShell 또는 명령 프롬프트를 열고 프로젝트 폴더로 이동합니다.
1. 의존성을 설치합니다.
     - `python -m pip install -r requirements.txt`
1. (선택) [SQL 파일](https://github.com/JJoriping/KKuTu/blob/master/db.sql)을 PostgreSQL 데이터베이스에 입력합니다.
     - 예시(관리자 권한 PowerShell): `psql -U postgres -d main -f .\db.sql`
1. 봇을 실행합니다.
     - `python app.py`
     - 종료는 `Ctrl + C`를 사용합니다.

#### 공통 설정
- PostgreSQL 연결을 위해 `settings.json`의 `PGSQL_CONFIG`의 `PG_PASS`를 반드시 환경에 맞게 수정해야 합니다.
- 만약 PostgreSQL을 사용하지 않는다면 `settings.json`의 `DB_PATH`을 데이터베이스로 사용하게 됩니다.
- 이 프로젝트는 [WordNet](https://wordnet.princeton.edu/)과 [JJoriping/KKuTu](https://github.com/JJoriping/KKuTu)의 단어 데이터를 참고하여 동작합니다.
- 최초 설치 후에는 각 환경의 실행 단계만 반복하면 됩니다.

### 명령어

- `/search [query] [is_regex] [theme] [limit]`: DB에서 단어를 검색합니다.
    - `query`: 검색할 단어
    - `is_regex`: `query`를 정규식으로 해석할지 여부
    - `theme`: 특정 테마 내에서 검색
    - `limit`: 검색 결과 개수 (최대값은 `settings.json`의 `SEARCH_RESULT_LIMIT`)
- `/mean [query]`: 단어의 뜻을 검색합니다.
    - `query`: 검색할 단어
- `/theme`: 추가 예정

## English

Not available yet.