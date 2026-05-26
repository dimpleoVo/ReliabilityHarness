class BaseTask:
    """
    所有任务的统一抽象接口
    """

    name = "base"

    # 主指标
    primary_metric = None

    # 辅指标
    secondary_metrics = []

    # 失效信号
    failure_signals = []

    def evaluate_primary(self, sample):
        """
        计算主指标
        """
        raise NotImplementedError

    def evaluate_secondary(self, sample):
        """
        计算辅助指标
        """
        results = {}

        for metric_fn in self.secondary_metrics:
            results[metric_fn.__name__] = metric_fn(sample)

        return results

    def detect_failure_signals(self, sample, primary_score):
        """
        判断 failure signals
        """
        signals = []

        for fn in self.failure_signals:
            if fn(sample, primary_score):
                signals.append(fn.__name__)

        return signals

    def map_to_risk_inputs(self, primary_score, secondary_results):
        """
        映射到统一 risk space
        """
        raise NotImplementedError