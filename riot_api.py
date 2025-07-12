import json
import requests

# 讀取設定檔
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

API_KEY = config["api_key"]
SUMMONER_NAME = config["summoner_name"]
REGION = config["region"] # 台灣在Riot 自營後為 "asia"
ROUTING = config["routing"]

# API 路徑範例：根據召喚師名稱查詢帳號資料
def get_account_by_riot_id(summoner_name, tag_line):
    # url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}"
    url = f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{summoner_name}/{tag_line}"
    headers = {"X-Riot-Token": API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()        
        return data

    else:
        print(f"查詢失敗，狀態碼：{response.status_code}")
        print(response.text)
        return None

# API 路徑範例：根據puuid查詢最近五場遊戲ID
def get_match_ids(puuid, count=20):
    url = f"https://{ROUTING}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    headers = {"X-Riot-Token": API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print("取得比賽 ID 失敗", response.status_code, response.text)
        return []


def get_match_detail(match_id, puuid):
    url = f"https://{ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {"X-Riot-Token": API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        match = response.json()
        participants = match["info"]["participants"]
        for p in participants:
            if p["puuid"] == puuid:
                return {
                    "champion": p["championName"],
                    "kills": p["kills"],
                    "deaths": p["deaths"],
                    "assists": p["assists"],
                    "win": p["win"],
                    "gameMode": match["info"]["gameMode"],
                    "position": p.get("individualPosition", "UNKNOWN")
                }
                break
    else:
        print(f"取得比賽 {match_id} 詳細失敗", response.status_code)
        return None

def get_active_player():
    try:
        res = requests.get("https://127.0.0.1:2999/liveclientdata/activeplayer", verify=False)
        if res.status_code == 200:
            data = res.json()
            print({data.get("summonerName")})
        else:
            print(f"失敗", res.status_code)
    except:
        return None