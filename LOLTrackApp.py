import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import io
import requests
from riot_api import get_account_by_riot_id, get_match_ids, get_match_detail
from collections import Counter

# 路線對應中文
POSITION_MAP = {
    "TOP": "上路",
    "JUNGLE": "打野",
    "MIDDLE": "中路",
    "BOTTOM": "下路",
    "UTILITY": "輔助",
    "UNKNOWN": "未知"
}

# 英雄圖基底URL（版本號可能需要跟 Data Dragon 版本同步）
CHAMPION_IMG_BASE = "https://ddragon.leagueoflegends.com/cdn/14.13.1/img/champion/"

def fetch_champion_image(champion_name):
    url = f"{CHAMPION_IMG_BASE}{champion_name}.png"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        img_data = resp.content
        pil_image = Image.open(io.BytesIO(img_data))
        pil_image = pil_image.resize((64, 64), Image.ANTIALIAS)
        return ImageTk.PhotoImage(pil_image)
    except:
        return None

class LOLTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LOL 戰績追蹤器")
        self.root.geometry("500x600")

        self.label = tk.Label(root, text="輸入召喚師名稱（含 Tag，例如：草莓糖水O口O#shuga）:")
        self.label.pack(pady=5)

        self.entry = tk.Entry(root, width=40)
        self.entry.pack(pady=5)
        self.entry.insert(0, "草莓糖水O口O#shuga")

        self.btn = tk.Button(root, text="更新戰績", command=self.update_stats)
        self.btn.pack(pady=10)

        self.stats_label = tk.Label(root, text="", font=("Arial", 12))
        self.stats_label.pack()

        self.canvas = tk.Canvas(root, width=480, height=450)
        self.canvas.pack()

        self.match_frames = []
        self.champion_imgs = []

    def clear_matches(self):
        for frame in self.match_frames:
            frame.destroy()
        self.match_frames = []
        self.champion_imgs = []
        self.canvas.delete("all")

    def update_stats(self):
        self.clear_matches()
        full_name = self.entry.get()
        if "#" not in full_name:
            messagebox.showerror("錯誤", "請輸入完整名稱，例如：草莓糖水O口O#shuga")
            return
        summoner_name, tag_line = full_name.split("#", 1)

        account = get_account_by_riot_id(summoner_name, tag_line)
        if not account:
            messagebox.showerror("錯誤", "查不到帳號，請檢查名稱與 Tag。")
            return
        puuid = account["puuid"]

        match_ids = get_match_ids(puuid, count=5)
        if not match_ids:
            messagebox.showinfo("提示", "查無最近對戰紀錄")
            return

        matches = []
        for mid in match_ids:
            detail = get_match_detail(mid, puuid)
            if detail:
                matches.append(detail)

        # 統計勝率與平均KDA
        total = len(matches)
        wins = sum(1 for m in matches if m['win'])
        win_rate = round((wins / total) * 100, 1)
        total_kda = 0
        for m in matches:
            deaths = max(1, m['deaths'])
            kda = (m['kills'] + m['assists']) / deaths
            total_kda += kda

        avg_kda = round(total_kda / len(matches), 2)

        self.stats_label.config(text=f"勝率: {win_rate}% | 平均 K/D/A: {avg_kda}")

        # 英雄使用次數統計
        heroes = [m['champion'] for m in matches]
        top_heroes = Counter(heroes).most_common(3)
        top_hero_text = "最多使用英雄： " + "  ".join([f"{hero} x{count}" for hero, count in top_heroes])

        # 統計路線（位置）
        positions = [m.get("position", "UNKNOWN") for m in matches]
        position_count = Counter(positions)    
        most_common_pos = position_count.most_common(1)
        if most_common_pos:
            pos_name, count = most_common_pos[0]
            pos_cn = POSITION_MAP.get(pos_name, "未知")
            position_text = f"常用路線：{pos_cn}（{count}場）"
        else:
            position_text = "常用路線：未知"

        # 顯示在 hero_label 下方
        if hasattr(self, 'position_label'):
            self.position_label.config(text=position_text)
        else:
            self.position_label = tk.Label(self.root, text=position_text, font=("Arial", 11))
            self.position_label.pack()

        # 顯示在 stats_label 下方
        if hasattr(self, 'hero_label'):
            self.hero_label.config(text=top_hero_text)
        else:
            self.hero_label = tk.Label(self.root, text=top_hero_text, font=("Arial", 11))
            self.hero_label.pack()

        # 顯示每場比賽詳細
        y = 10
        for match in matches:
            frame = tk.Frame(self.canvas, bd=2, relief="groove")
            frame.place(x=10, y=y, width=460, height=80)
            self.match_frames.append(frame)

            img = fetch_champion_image(match["champion"])
            self.champion_imgs.append(img)  # Tkinter 需保持 reference

            img_label = tk.Label(frame, image=img)
            img_label.pack(side="left", padx=5)

            text = f"{match['champion']}  {match['kills']}/{match['deaths']}/{match['assists']}  "
            text += "勝利" if match['win'] else "失敗"
            text += f"  模式: {match['gameMode']}"

            label = tk.Label(frame, text=text, font=("Arial", 12))
            label.pack(side="left")

            # 勝敗文字顏色
            label.config(fg="green" if match['win'] else "red")

            y += 90

if __name__ == "__main__":
    root = tk.Tk()
    app = LOLTrackerApp(root)
    root.mainloop()
