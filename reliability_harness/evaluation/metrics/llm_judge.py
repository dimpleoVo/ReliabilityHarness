import random

def get_llm_judge_score(gt, pred, judge_config):
    """
    Mock 裁判逻辑：模拟 DeepSeek 打分。
    当 judge_config 中 mock 为 True 时，生成模拟分数。
    """
    if judge_config.get("mock", False):
        # 简单的 Mock 逻辑：如果有预测结果，给一个 0.7-0.95 的随机分
        if not pred or len(pred.strip()) == 0:
            return 0.0
        return round(random.uniform(0.7, 0.95), 2)

    # 这里预留真实 API 调用，以后接上 Key 就能用
    # return _call_openai_compat(...)
    return 0.0