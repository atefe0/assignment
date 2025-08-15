import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

np.random.seed(42)

num_days = 90
num_users = 100
events = ["login", "play_video", "like", "comment", "logout"]
platforms = ["web", "ios", "android"]

dates = pd.date_range(start="2025-05-01", periods=num_days, freq="D")
data = []

event_id_counter = 1
for day in dates:
    for _ in range(np.random.randint(50, 150)):
        event_type = np.random.choice(events, p=[0.2, 0.4, 0.2, 0.1, 0.1])
        user_id = np.random.randint(1, num_users+1)
        platform = np.random.choice(platforms)
        video_id = np.random.randint(1, 50) if event_type in ["play_video", "like", "comment"] else None
        watch_time_sec = np.random.randint(5, 500) if event_type == "play_video" else None
        video_duration = np.random.randint(60, 600) if event_type == "play_video" else None

        data.append([
            event_id_counter,
            user_id,
            day + pd.Timedelta(seconds=np.random.randint(0, 86400)),
            platforms,
            event_type,
            video_id,
            watch_time_sec,
            video_duration
        ])
        event_id_counter += 1

df = pd.DataFrame(data, columns=[
    "event_id", "user_id", "timestamp", "platform", "event_type",
    "video_id", "watch_time_sec", "video_duration_sec"
])

df["timestamp"] = pd.to_datetime(df["timestamp"])

score_map = {
    "comment": 5,
    "like": 3,
    "play_video": 1,
    "login": 0,
    "logout": 0
}

df["engagement_score"] = df["event_type"].map(score_map).fillna(0).astype(int)
df["engagement_score"] = pd.to_numeric(df["engagement_score"], errors="coerce").fillna(0)

df["date"] = df["timestamp"].dt.date

for col in ["date", "platform", "event_type"]:
    df[col] = df[col].apply(lambda x: x[0] if isinstance(x, list) else x)

daily_engagement = (
    df.groupby(["date", "platform"], as_index=False)["engagement_score"]
    .sum()
    .reset_index()
)

heatmap_data = daily_engagement.pivot(index="date", columns="platform", values="engagement_score").fillna(0)

plt.figure(figsize=(12,8))
sns.heatmap(
    heatmap_data,
    cmap="Greys",
    linewidths=0.5,
    linecolor="gray"
)

plt.title("Daily Engagement Score by Platform", fontsize=16)
plt.xlabel("Platform", fontsize=14)
plt.ylabel("Date", fontsize=14)
plt.tight_layout()
plt.show()
