import json

transcript_path = r"C:\Users\HP\.gemini\antigravity-ide\brain\f7c87b19-54cf-48a2-bdaf-8ac8e8d07811\.system_generated\logs\transcript_full.jsonl"

matches = []
with open(transcript_path, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        if "Build order" in line or "A1" in line:
            try:
                data = json.loads(line)
                matches.append((idx, data.get("step_index"), data.get("source"), data.get("type")))
            except Exception as e:
                pass

print(f"Total matches for A1 / Build order: {len(matches)}")
for m in matches[:50]:
    print(m)
