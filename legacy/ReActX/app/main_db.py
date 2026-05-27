# app/main.py

from app.loop.closed_loop_runner import run_closed_loop

if __name__ == "__main__":
    print("🚀 RUNNING ReActX CLOSED LOOP...")

    result = run_closed_loop(
        "Write a Python function to sort a list"
    )

    print("\n📊 FINAL RESULT:")
    print(result)