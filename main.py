
# 넷플릭스 추천 시스템 - 3가지 추천 모드 + 5가지 시각화
# 포함된 그래프: barplot, audience_vs_critic, score_distribution, votes_vs_score, title_wordcloud

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import zscore
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from wordcloud import WordCloud
from collections import Counter

df = pd.read_csv("data/netflix-rotten-tomatoes-metacritic-imdb.csv")
df.rename(columns={"IMDb Score": "IMDb", "Metacritic Score": "Metacritic"}, inplace=True)
df["Release Year"] = pd.to_datetime(df["Release Date"], errors="coerce").dt.year
df = df.dropna(subset=["IMDb", "IMDb Votes", "Title", "Genre", "Release Year"])
df["IMDb Votes"] = pd.to_numeric(df["IMDb Votes"], errors="coerce")
df["Metacritic"] = pd.to_numeric(df["Metacritic"], errors="coerce")
df["Hidden Gem Score"] = df["IMDb"] / (df["IMDb Votes"] ** 0.1)
df["Z_HiddenGem"] = zscore(df["Hidden Gem Score"])
df["Z_IMDb"] = zscore(df["IMDb"])
df["Z_Votes"] = zscore(df["IMDb Votes"])

save_path = Path("image") / datetime.now().strftime("%y%m%d%H%M%S")
save_path.mkdir(parents=True, exist_ok=True)

root = tk.Tk()
root.title("넷플릭스 콘텐츠 추천")

tk.Label(root, text="장르 선택").grid(row=0, column=0)
genre_var = tk.StringVar(value="Drama")
tk.OptionMenu(root, genre_var, "Action", "Adult", "Adventure", "Animation", "Biography", "Comedy", "Crime",
              "Documentary", "Drama", "Family", "Fantasy", "Film-Noir", "Game-Show", "History", "Horror",
              "Music", "Musical", "Mystery", "News", "Reality-TV", "Romance", "Sci-Fi", "Short", "Sport",
              "Talk-Show", "Thriller", "War", "Western").grid(row=0, column=1)

tk.Label(root, text="연도 (최소)").grid(row=1, column=0)
entry_year_min = tk.Entry(root)
entry_year_min.insert(0, "2000")
entry_year_min.grid(row=1, column=1)

tk.Label(root, text="연도 (최대)").grid(row=2, column=0)
entry_year_max = tk.Entry(root)
entry_year_max.insert(0, "2024")
entry_year_max.grid(row=2, column=1)

tk.Label(root, text="추천 기준").grid(row=3, column=0)
mode_var = tk.StringVar(value="모드 선택")
tk.OptionMenu(root, mode_var, "숨겨진 명작", "인기 작품", "비평가 추천").grid(row=3, column=1)

def recommend():
    genre = genre_var.get()
    year_min = entry_year_min.get().strip()
    year_max = entry_year_max.get().strip()
    mode = mode_var.get()

    filtered = df.copy()
    filtered = filtered[filtered["Genre"].str.contains(genre, na=False)]
    if year_min:
        filtered = filtered[filtered["Release Year"] >= int(year_min)]
    if year_max:
        filtered = filtered[filtered["Release Year"] <= int(year_max)]

    score_col = ""
    top = pd.DataFrame()

    if mode == "추천 기준 선택":
        messagebox.showinfo("선택 오류", "추천 기준을 선택하세요.")
        return
    elif mode == "숨겨진 명작":
        score_col = "Hidden Gem Score"
        filtered = filtered[filtered["Z_HiddenGem"].abs() < 2]
        filtered = filtered[filtered[score_col] >= 1.0]
        top = filtered.sort_values(by=score_col, ascending=False).head(10)
    elif mode == "인기 작품":
        score_col = "IMDb"
        filtered = filtered[filtered["Z_IMDb"].abs() < 2]
        filtered = filtered[filtered["IMDb"] >= 7.5]
        filtered = filtered[filtered["IMDb Votes"] >= 5000]
        top = filtered.sort_values(by=score_col, ascending=False).head(10)
    elif mode == "비평가 추천":
        score_col = "Metacritic"
        filtered = filtered.dropna(subset=["Metacritic"])
        filtered = filtered[filtered["Metacritic"] >= 70]
        top = filtered.sort_values(by=score_col, ascending=False).head(10)
    else:
        messagebox.showinfo("선택 오류", "추천 기준을 선택하세요.")
        return

    if top.empty:
        messagebox.showinfo("결과 없음", "조건에 맞는 추천 결과가 없습니다.")
        return

    
    # Convert mode to English for graph titles
    if mode == "숨겨진 명작":
        title_mode = "Hidden Gem"
    elif mode == "인기 작품":
        title_mode = "Popular"
    elif mode == "비평가 추천":
        title_mode = "Critic's Pick"

    print("\n===== 추천 결과 =====")
    print(top[["Title", "Release Year", score_col]])
    text_output_path = save_path / "recommendation_result.txt"
    top[["Title", "Release Year", score_col]].to_string(buf=open(text_output_path, "w", encoding="utf-8"))

    # 1. Barplot
    plt.figure(figsize=(10, 6))
    sns.barplot(x=score_col, y="Title", data=top, orient="h")
    plt.title(f"Top 10 Recommendations - {title_mode}")
    plt.tight_layout()
    plt.savefig(save_path / "barplot.png")
    plt.close()

    # 2. Audience vs Critic
    filtered_mc = filtered.dropna(subset=["Metacritic"])
    if not filtered_mc.empty:
        plt.figure(figsize=(8, 6))
        
    # 2. Audience vs Critic (Top 10 Only)
    if not top.dropna(subset=["Metacritic"]).empty:
        plt.figure(figsize=(8, 6))
        sns.scatterplot(data=top, x="IMDb", y="Metacritic", alpha=0.7)
        for i in range(len(top)):
            plt.text(top["IMDb"].iloc[i], top["Metacritic"].iloc[i],
                     top["Title"].iloc[i][:15], fontsize=7, alpha=0.6)
        plt.title("Audience vs Critic: IMDb vs Metacritic")
        plt.tight_layout()
        plt.savefig(save_path / "audience_vs_critic.png")
        plt.close()
    
        plt.close()

    # 3. Score Distribution
    plt.figure(figsize=(8, 4))
    sns.histplot(filtered[score_col], bins=20, kde=True)
    plt.title(f"{score_col} Distribution - {title_mode}")
    plt.tight_layout()
    plt.savefig(save_path / "score_distribution.png")
    plt.close()

    # 4. Votes vs Score (Top 10 Only)
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=top, x="IMDb Votes", y=score_col, alpha=0.6)
    for i in range(len(top)):
        plt.text(top["IMDb Votes"].iloc[i], top[score_col].iloc[i],
                 top["Title"].iloc[i][:15], fontsize=7, alpha=0.6)
    plt.title(f"Votes vs {score_col} ({title_mode})")
    plt.tight_layout()
    plt.savefig(save_path / "votes_vs_score.png")
    plt.close()
    
    plt.close()

    # 5. WordCloud from Top Titles
    titles = top["Title"].tolist()
    word_freq = Counter(titles)
    wordcloud = WordCloud(width=800, height=400, background_color='white', collocations=False).generate_from_frequencies(word_freq)
    wordcloud.to_file(save_path / "title_wordcloud.png")

    messagebox.showinfo("완료", f"추천 결과 및 그래프가 저장되었습니다:\n{save_path}")

tk.Button(root, text="추천 실행", command=recommend).grid(row=4, column=0, columnspan=2)
root.mainloop()
