# To run this code you need to install the following dependencies:
# pip install google-genai

import os
import re

import srt
from google import genai
from google.genai import types


def translate(model: str, content: str) -> str:
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=content)],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=-1,
        ),
        system_instruction=[
            types.Part.from_text(
                text="""I want to translate this subtitle of a statistics lecture into vietnamese, just return best translation"""
            ),
        ],
    )

    result = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.text is not None:
            result += chunk.text

    return result


# Dummy translator for demonstration (replace with real one)
def translate_text(text: str) -> str:
    # Replace with real translation logic (Google Translate API, Gemini, etc.)
    return text.upper()  # Simulate translation


# Updated sentence splitter: also split at ',', 'and'
def split_sentences(text):
    # Split at punctuation or "and" with proper word boundaries
    parts = re.split(r"(?<=[.!?,])\s+|(?i)(?<=\b)and(?=\b)", text)
    return [p.strip() for p in parts if p.strip()]


def proportional_sentence_split(translated_sentences, original_texts):
    original_lengths = [len(t) for t in original_texts]
    total_length = sum(original_lengths)
    proportions = [l / total_length for l in original_lengths]

    output_chunks = [""] * len(original_texts)
    sent_index = 0

    for i, prop in enumerate(proportions):
        target_chars = round(prop * sum(len(s) for s in translated_sentences))
        acc = ""
        while (
            sent_index < len(translated_sentences)
            and len(acc) + len(translated_sentences[sent_index]) <= target_chars
        ):
            acc += translated_sentences[sent_index] + " "
            sent_index += 1
        output_chunks[i] = acc.strip()

    # Put leftover sentences in the last chunk
    for i in range(sent_index, len(translated_sentences)):
        output_chunks[-1] += " " + translated_sentences[i].strip()

    return output_chunks


def process_subtitles(input_srt_path: str, output_srt_path: str):
    with open(input_srt_path, "r", encoding="utf-8") as f:
        subs = list(srt.parse(f.read()))

    original_texts = [sub.content for sub in subs]
    combined_text = " ".join(original_texts)
    translated_full = translate_text(combined_text)
    translated_sentences = split_sentences(translated_full)
    translated_chunks = proportional_sentence_split(
        translated_sentences, original_texts
    )

    new_subs = []
    for orig, translated in zip(subs, translated_chunks):
        new_subs.append(
            srt.Subtitle(
                index=orig.index, start=orig.start, end=orig.end, content=translated
            )
        )

    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(new_subs))


# Example usage
if __name__ == "__main__":
    input_srt = "../video_trans/lec17.srt"
    output_srt = "out.srt"
    process_subtitles(input_srt, output_srt)
    # print(translate(model="gemini-2.5-pro", content="hello"))
