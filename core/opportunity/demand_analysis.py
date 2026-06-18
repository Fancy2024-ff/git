"""core.opportunity.demand_analysis — 需求强度分析。

单一事实源：需求评分规则只在这里。runner 调用 analyze_demand。
"""

from __future__ import annotations


def analyze_demand(app: dict) -> dict:
    """需求分析：多维度评估需求强度。"""
    downloads = app.get("downloads", 0)
    rating = app.get("rating", 0)
    review_count = app.get("review_count", 0)
    monetization = app.get("monetization", "")
    features = app.get("features", [])

    # 下载量评分 (0-30)
    if downloads > 5_000_000: dl_score = 30
    elif downloads > 2_000_000: dl_score = 25
    elif downloads > 500_000: dl_score = 18
    elif downloads > 100_000: dl_score = 12
    else: dl_score = 5

    # 评分评分 (0-20)
    rating_score = int(min(20, rating * 4.2))

    # 评论数评分 (0-15)
    if review_count > 10000: rev_score = 15
    elif review_count > 3000: rev_score = 12
    elif review_count > 500: rev_score = 8
    else: rev_score = 4

    # 变现验证 (0-15)
    if monetization in ("subscription", "freemium"): mon_score = 15
    elif monetization == "paid": mon_score = 12
    else: mon_score = 5

    # 功能丰富度 (0-10)
    feat_score = min(10, len(features) * 2)

    # 持续更新（本地无法判断，给默认分）
    update_score = 10

    demand_score = dl_score + rating_score + rev_score + mon_score + feat_score + update_score

    return {
        "app_name": app["name"],
        "app_name_cn": app["name_cn"],
        "demand_score": min(100, demand_score),
        "score_breakdown": {
            "downloads_score": dl_score,
            "rating_score": rating_score,
            "review_count_score": rev_score,
            "monetization_score": mon_score,
            "feature_richness_score": feat_score,
            "update_frequency_score": update_score,
        },
        "target_users": f"需要{app['name_cn'].replace('AI ', '')}功能的移动用户",
        "pain_point": "原生 App 需要下载安装，小程序可即用即走",
        "market_validation": f"{downloads:,} 次下载、{rating} 分评分证明需求真实存在",
        "conclusion": "需求已被市场验证" if demand_score >= 60 else "需求待进一步验证",
    }
