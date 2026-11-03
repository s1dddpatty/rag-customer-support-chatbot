import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


def extract_fallback_answer(prompt: str) -> str:
    """Fallback answer generator when Ollama is not running."""
    context = ""
    question = ""

    if "CONTEXT:" in prompt and "QUESTION:" in prompt:
        parts = prompt.split("CONTEXT:")[1].split("QUESTION:")
        context = parts[0].strip()
        question = parts[1].split("ANSWER:")[0].strip()

    if not context or not question:
        return "I don't have that information in the documentation."

    source_blocks = re.split(r"\[Source (\d+)\]", context)
    candidates = []

    q_words = set(re.findall(r"\w+", question.lower())) - {
        "what", "is", "the", "how", "to", "can", "i", "a", "an", "in", "for", "of", "and", "do", "does", "my", "you", "are", "we", "our"
    }

    if len(source_blocks) >= 3:
        for idx in range(1, len(source_blocks), 2):
            source_num = source_blocks[idx]
            block_text = source_blocks[idx + 1].strip() if idx + 1 < len(source_blocks) else ""
            if not block_text:
                continue

            lines = [line.strip() for line in block_text.split("\n") if line.strip()]
            matching_lines = []
            score = 0
            for line in lines:
                line_words = set(re.findall(r"\w+", line.lower()))
                overlap = len(q_words & line_words)
                if overlap > 0:
                    score += overlap
                    matching_lines.append(line)

            if matching_lines:
                text_ans = " ".join(matching_lines[:3])
                candidates.append((score, f"{text_ans} [Source {source_num}]"))
            elif block_text:
                candidates.append((0, f"{block_text[:140]}... [Source {source_num}]"))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_score = candidates[0][0]
        if best_score > 0:
            top_matches = [c[1] for c in candidates if c[0] == best_score or c[0] > 0][:2]
            return "\n\n".join(top_matches)
        return candidates[0][1]

    return "I don't have that information in the documentation."


def generate_answer(prompt: str):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=3
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("response", "")
    except Exception:
        pass

    # Fallback to extractive answer from prompt context
    return extract_fallback_answer(prompt)
