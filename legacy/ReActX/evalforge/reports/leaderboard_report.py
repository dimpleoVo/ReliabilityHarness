def generate_leaderboard_html(path, summaries, slice_keys):
    html = """
    <html>
    <head>
    <meta charset="UTF-8">
    <title>EvalForge Leaderboard</title>
    <style>
    body {
        font-family: Arial, sans-serif;
        margin: 40px;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 40px;
    }
    th, td {
        border: 1px solid #ccc;
        padding: 10px;
        text-align: left;
    }
    th {
        background: #f2f2f2;
    }
    h1, h2 {
        margin-top: 24px;
    }
    </style>
    </head>
    <body>
    <h1>EvalForge Leaderboard</h1>
    """

    html += """
    <h2>Overall Metrics</h2>
    <table>
      <tr>
        <th>Model</th>
        <th>Samples</th>
        <th>Edit Distance</th>
        <th>LLM Judge</th>
        <th>Invalid Outputs</th>
        <th>Badcases</th>
      </tr>
    """

    for item in summaries:
        html += f"""
        <tr>
          <td>{item['model_name']}</td>
          <td>{item['num_samples']}</td>
          <td>{item['overall_edit_distance']:.6f}</td>
          <td>{item['overall_llm_judge_score']:.6f}</td>
          <td>{item['num_invalid_outputs']}</td>
          <td>{item['num_badcases']}</td>
        </tr>
        """

    html += "</table>"

    for slice_key in slice_keys:
        html += f"<h2>Slice: {slice_key}</h2>"

        all_buckets = set()
        for item in summaries:
            all_buckets.update(item["slice_analysis"].get(slice_key, {}).keys())

        all_buckets = sorted(all_buckets)

        html += "<table><tr><th>Model</th>"
        for bucket in all_buckets:
            html += f"<th>{bucket}</th>"
        html += "</tr>"

        for item in summaries:
            html += f"<tr><td>{item['model_name']}</td>"
            slice_data = item["slice_analysis"].get(slice_key, {})
            for bucket in all_buckets:
                value = slice_data.get(bucket, "N/A")
                if isinstance(value, float):
                    html += f"<td>{value:.6f}</td>"
                else:
                    html += f"<td>{value}</td>"
            html += "</tr>"

        html += "</table>"

    html += "</body></html>"

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)