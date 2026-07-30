import os
from datetime import datetime


def save_and_print_log(state: dict, log_dir: str = "run_logs"):
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(log_dir, f"log_{timestamp}.md")

    md_lines = []
    md_lines.append("# 🕵️ SQL Agent Execution Log\n")
    md_lines.append(f"**❓ User Question:** {state.get('question')}\n")

    md_lines.append("## 🧠 Thought Process\n")

    history = state.get("history", [])
    if not history:
        md_lines.append("*No history recorded.*\n")

    for step in history:
        attempt = step["attempt"]
        is_appr_emoji = "✅" if step["is_approved"] else "❌"
        is_valid_emoji = "✅" if step["is_valid"] else "❌"

        md_lines.append(f"### 🔄 Attempt {attempt}")
        md_lines.append(f"**Generated SQL:**\n```sql\n{step['query']}\n```")
        md_lines.append(
            f"**DB Result (Valid: {is_valid_emoji}):**\n```text\n{step['db_result']}\n```"
        )
        md_lines.append(f"**Critic Reasoning:** {step['critic_reasoning']}")
        md_lines.append(f"**Critic Feedback:** {step['critic_feedback']}")
        md_lines.append(f"**Approved by Critic:** {is_appr_emoji}\n")
        md_lines.append("---\n")

    md_lines.append("## 🎯 Final Output\n")
    md_lines.append(f"**Answer:**\n{state.get('final_answer')}\n")

    full_text = "\n".join(md_lines)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_text)

    print("\n" + "=" * 50)
    print(" 🚀 AGENT EXECUTION FINISHED ")
    print("=" * 50)
    print(f"❓ Question: {state.get('question')}")
    print(f"🔄 Total attempts: {len(history)}")
    print(f"🎯 Final Answer: {state.get('final_answer')}")
    print("=" * 50)
    print(f"📂 Full history saved to: {filepath}\n")
