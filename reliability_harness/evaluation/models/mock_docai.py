def predict(sample):
    """
    模拟一个 DocAI 模型预测
    """

    # sample 是 dataset 中的一条数据
    sid = sample["id"]

    # 模拟不同情况

    # case1: 系统失败
    if sid == "doc1":
        return "Sorry, I can't assist with that."

    # case2: 正确识别
    if sid == "doc2":
        return "# Title\n\nThis is english paragraph"

    # case3: 识别错误
    return "# 表格\n\n|A|B|\n|-|-|\n|1|X|"