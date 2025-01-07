import tkinter as tk
from tkinter import messagebox, filedialog
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.dates import DateFormatter
import jpholiday

# Attempt to load Osaka font
jp_font_path = next((f for f in fm.findSystemFonts() if "Osaka" in f), None)
jp_font = fm.FontProperties(fname=jp_font_path) if jp_font_path else fm.FontProperties()

def get_working_days_duration(start_date, days):
    current_date = start_date
    working_days = 0
    total_days = 0

    while working_days < days:
        if current_date.weekday() < 5 and not jpholiday.is_holiday(current_date):
            working_days += 1
        current_date += pd.Timedelta(days=1)
        total_days += 1

    return total_days

def create_gantt_chart(task_durations, start_date):
    tasks = list(task_durations.keys())
    durations = list(task_durations.values())
    
    df = pd.DataFrame({"Task": tasks, "Duration": durations})
    df["Start"] = pd.NaT
    df["End"] = pd.NaT

    for i, task in enumerate(df["Task"]):
        if i == 0:  # 最初のタスクの開始日を設定
            df.loc[i, "Start"] = start_date
        elif i > 0:
            if pd.isna(df.loc[i - 1, "End"]):
                messagebox.showerror("データエラー", f"タスク '{df.loc[i - 1, 'Task']}' の終了日が設定されていません。")
                print("デバッグ: データフレームの内容")
                print(df)
                return
            df.loc[i, "Start"] = df.loc[i - 1, "End"]

        if pd.isna(df.loc[i, "Start"]):
            messagebox.showerror("データエラー", f"タスク '{task}' の開始日が設定されていません。")
            print("デバッグ: データフレームの内容")
            print(df)
            return

        df.loc[i, "End"] = pd.Timestamp(df.loc[i, "Start"])
        total_days = 0

        while total_days < df.loc[i, "Duration"]:
            df.loc[i, "End"] += pd.Timedelta(days=1)
            total_days += 1

    chart_start_date = start_date - pd.Timedelta(days=5)
    chart_end_date = df["End"].max() + pd.Timedelta(days=5)

    fig, ax = plt.subplots(figsize=(16, 8))

    y_positions = range(len(df))

    for i, task in enumerate(df["Task"]):
        if pd.isna(df.loc[i, "Start"]):
            continue  # Skip tasks with missing start dates

        ax.barh(y_positions[i], (df.loc[i, "End"] - df.loc[i, "Start"]).days, left=df.loc[i, "Start"].toordinal(), color="skyblue")
        ax.text(df.loc[i, "Start"].toordinal(), y_positions[i], df.loc[i, "Start"].strftime('%m-%d'),
                va='center', ha='right', fontsize=8, fontproperties=jp_font)
        ax.text(df.loc[i, "End"].toordinal(), y_positions[i], df.loc[i, "End"].strftime('%m-%d'),
                va='center', ha='left', fontsize=8, fontproperties=jp_font)

    date_range = pd.date_range(start=chart_start_date, end=chart_end_date, freq="D")
    for date in date_range:
        if date.weekday() >= 5 or jpholiday.is_holiday(date):
            ax.axvspan(date.toordinal(), date.toordinal() + 1, color="lightgray", alpha=0.3)

    ax.set_xlim(chart_start_date.toordinal(), chart_end_date.toordinal())
    ax.set_xlabel("日付", fontproperties=jp_font)
    ax.set_ylabel("タスク", fontproperties=jp_font)
    ax.set_title("建築プロジェクトのガントチャート", fontproperties=jp_font)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(df["Task"], fontproperties=jp_font)
    ax.xaxis.set_major_formatter(DateFormatter('%m-%d'))

    plt.tight_layout()

    png_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
    if png_path:
        fig.savefig(png_path)
        messagebox.showinfo("成功", f"ガントチャートを保存しました: {png_path}")

def on_generate_chart():
    try:
        start_date_input = start_date_entry.get().strip()
        if not start_date_input:
            raise ValueError("着手日が入力されていません。")
        start_date = pd.Timestamp(start_date_input)

        task_durations = {}
        for task, duration_entry in task_entries.items():
            duration_input = duration_entry.get().strip()
            if duration_input:
                try:
                    task_durations[task] = get_working_days_duration(start_date, int(duration_input))
                except ValueError:
                    messagebox.showerror("入力エラー", f"タスク '{task}' の作業日数が無効です。整数を入力してください。")
                    return

        if not task_durations:
            raise ValueError("タスクの作業日数が入力されていません。")

        create_gantt_chart(task_durations, start_date)
    except ValueError as ve:
        messagebox.showerror("入力エラー", f"{ve}")
    except Exception as e:
        messagebox.showerror("エラー", f"入力データに問題があります: {e}")

root = tk.Tk()
root.title("ガントチャート作成ツール")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

tk.Label(frame, text="着手日 (YYYY-MM-DD):").grid(row=0, column=0, sticky="e")
start_date_entry = tk.Entry(frame)
start_date_entry.grid(row=0, column=1, pady=5)

# Task input fields
task_entries = {}
tasks = ["事前協議", "設計図書作成", "構造計算", "省エネ計算", "申請書類作成", "チェック", "修正", "提出", "事前審査", "訂正", "最終審査", "申請済予定"]

for i, task in enumerate(tasks):
    tk.Label(frame, text=f"{task}作業日数:").grid(row=i+1, column=0, sticky="e")
    task_entry = tk.Entry(frame)
    task_entry.grid(row=i+1, column=1, pady=5)
    task_entries[task] = task_entry

generate_button = tk.Button(root, text="ガントチャート生成", command=on_generate_chart)
generate_button.pack(pady=10)

root.mainloop()
