# app/main.py

from app.loop.closed_loop_runner import run_closed_loop

if __name__ == "__main__":
    print("🚀 RUNNING ReActX CLOSED LOOP...")

    tasks = [
        "sort a list",
        "reverse a string",
        "find max value",
        "write fibonacci",
        "sum a list"
    ]

    for task in tasks:
        print(f"\n=== TASK: {task} ===")
        result = run_closed_loop(task)
        print(result)