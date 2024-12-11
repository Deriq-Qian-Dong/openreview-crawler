import pandas as pd
import numpy as np

# 从 CSV 文件读取数据
file_path = "accepted_papers_with_scores.csv"
df = pd.read_csv(file_path)

# 打印数据以确认加载正确
print(df)

# 将分数列转换为数值数组
def parse_scores(scores):
    # 处理 NaN 值
    if pd.isnull(scores):
        return np.array([0])
    return np.array(list(map(float, scores.split(", "))))

df["novelty_scores"] = df["novelty_scores"].apply(parse_scores)
df["scope_scores"] = df["scope_scores"].apply(parse_scores)
df["technical_scores"] = df["technical_scores"].apply(parse_scores)

# 计算每条样本的分数平均值
df["novelty_avg"] = df["novelty_scores"].apply(np.mean)
df["scope_avg"] = df["scope_scores"].apply(np.mean)
df["technical_avg"] = df["technical_scores"].apply(np.mean)

# 按 track 统计信息
track_statistics = []
for track, group in df.groupby("track"):
    novelty_avg = group["novelty_avg"].mean()
    novelty_max = group["novelty_avg"].max()
    novelty_min = group["novelty_avg"].min()
    novelty_median = group["novelty_avg"].median()

    scope_avg = group["scope_avg"].mean()
    scope_max = group["scope_avg"].max()
    scope_min = group["scope_avg"].min()
    scope_median = group["scope_avg"].median()

    technical_avg = group["technical_avg"].mean()
    technical_max = group["technical_avg"].max()
    technical_min = group["technical_avg"].min()
    technical_median = group["technical_avg"].median()

    track_statistics.append({
        "track": track,
        "novelty_avg": novelty_avg,
        "novelty_max": novelty_max,
        "novelty_min": novelty_min,
        "novelty_median": novelty_median,
        "scope_avg": scope_avg,
        "scope_max": scope_max,
        "scope_min": scope_min,
        "scope_median": scope_median,
        "technical_avg": technical_avg,
        "technical_max": technical_max,
        "technical_min": technical_min,
        "technical_median": technical_median
    })

# 转换为 DataFrame
track_stats_df = pd.DataFrame(track_statistics)

# 输出结果
print(track_stats_df)

# 如果需要保存到文件
output_file = "track_statistics.csv"
track_stats_df.to_csv(output_file, index=False)
print(f"Track statistics saved to {output_file}")
