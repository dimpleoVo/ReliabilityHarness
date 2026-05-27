class RetryController:
    def __init__(self, max_steps=3):
        self.max_steps = max_steps

    def should_stop(self, eval_result, step):
        # 超过最大轮数
        if step >= self.max_steps:
            return True

        # 没有 GT，只能根据 runtime 决定
        if eval_result.get("no_gt", False):
            return not eval_result.get("runtime_error", False)

        # 成功条件：无 runtime_error 且 edit_distance 足够小
        if not eval_result.get("runtime_error", False):
            score = eval_result.get("metrics", {}).get("edit_distance")
            if score is not None and score <= 0.2:
                return True

        return False

    def should_retry(self, eval_result):
        # 没有 GT：只在 runtime error 时 retry
        if eval_result.get("no_gt", False):
            return eval_result.get("runtime_error", False)

        # runtime error 必 retry
        if eval_result.get("runtime_error", False):
            return True

        score = eval_result.get("metrics", {}).get("edit_distance")
        if score is None:
            return False

        # semantic error retry
        if score > 0.2:
            return True

        return False

    def get_strategy(self, eval_result):
        if eval_result.get("runtime_error", False):
            return "runtime_fix"

        if eval_result.get("no_gt", False):
            return "none"

        score = eval_result.get("metrics", {}).get("edit_distance")
        if score is not None and score > 0.2:
            return "semantic_fix"

        return "none"