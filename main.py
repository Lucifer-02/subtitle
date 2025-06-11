import re
from typing import List, Iterable
from pathlib import Path

import click
import srt # Import the srt package


def replace_sub(subtitles: Iterable[srt.Subtitle], translations: List[str]) -> str:
    """Replaces the text content of subtitles with provided translations."""
    # Convert subtitles iterator to list to check length and iterate multiple times if needed
    subtitles_list = list(subtitles)
    if len(translations) != len(subtitles_list):
         assert len(translations) == len(subtitles_list), \
            f'Number of translations ({len(translations)}) must match number of subtitles ({len(subtitles_list)})'

    translated_subtitles = []
    # Iterate through translations and original subtitles simultaneously
    for original_subtitle, translation in zip(subtitles_list, translations):
        # Create a new subtitle object with the translated content
        translated_subtitle = srt.Subtitle(
            index=original_subtitle.index,
            start=original_subtitle.start,
            end=original_subtitle.end,
            content=translation, # Use the translated content
            proprietary=original_subtitle.proprietary # Keep proprietary tags if any
        )
        translated_subtitles.append(translated_subtitle)


    # Use srt.compose to serialize the translated subtitles back into an SRT string
    return srt.compose(translated_subtitles)


def extract_content(subtitle_content: str) -> List[str]:
    """Extracts the text content from an SRT string using the srt package and replaces newlines with spaces."""
    # Use srt.parse to parse the SRT content into Subtitle objects
    subtitles = srt.parse(subtitle_content)
    # Extract content, replace newlines with spaces, and return as a list
    return [subtitle.content.replace('\n', ' ') for subtitle in subtitles]


def is_end_sentence(text: str) -> bool:
    """Checks if a string ends with punctuation indicating the end of a sentence."""
    return re.search(r"\w[.!?]$", text.strip()) is not None


def split(content: List[str], limit: int = 10) -> List[List[str]]:
    """Splits a list of strings into chunks, trying to break at sentence ends."""
    start_idx = 0
    end_idx = 0
    idx = 0
    parts = []

    while idx < len(content):
        current_chunk = content[start_idx : idx + 1]

        if len(current_chunk) >= limit:
            found_split_point = False
            for i in range(idx, start_idx - 1, -1):
                if is_end_sentence(content[i]):
                    end_idx = i
                    found_split_point = True
                    break
            if not found_split_point:
                 end_idx = idx

            if end_idx >= start_idx:
                 parts.append(content[start_idx : end_idx + 1])
                 start_idx = end_idx + 1

        idx += 1

    if start_idx < len(content):
        parts.append(content[start_idx:])

    return parts


@click.group()
def cli():
    """Subtitle Processing CLI"""
    pass


@cli.command()
@click.option("--srt-file", type=click.Path(exists=True), help="Path to the original SRT file")
@click.option("--limit", default=70, help="Limit of subtitle entries per chunk for translation")
@click.option("--output-dir", default=".", help="Directory to write prompt files")
@click.option(
    "--prompt-template",
    default='The following paragraph is the transcript (from srt file) of Statistics 21 UC Berkeley lecture, translate it into Vietnamese, do not remove "|" characters, It is used to separate subtitles: \n"{content}"',
    help="Template for the translation prompt. Use {content} as a placeholder for the subtitle chunk.",
)
def gen_prompts(srt_file: Path, limit, output_dir, prompt_template: str):
    """Generate translation prompts from SRT file."""
    srt_path = Path(srt_file)
    with srt_path.open("r", encoding='utf-8') as f:
        sub_content = f.read()
        all_content = extract_content(sub_content) # extract_content now replaces newlines

        parts = split(all_content, limit=limit)

        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True) # Ensure output directory exists

        for i, content_chunk in enumerate(parts):
            out_path = output_dir_path / f"prompt{i:03d}.txt" # Added zero-padding to filename
            with out_path.open("w", encoding='utf-8') as f_out: # Added encoding
                # Use the prompt_template from the command line argument
                prompt_text = prompt_template.replace("{content}", "|".join(content_chunk))
                f_out.write(prompt_text)


    click.echo(
        f"Generated {len(parts)} prompt files in {output_dir}, please use llm to translate this and paste into a txt file!"
    )


@cli.command()
@click.option("--srt-file", type=click.Path(exists=True), help="Path to the original SRT file")
@click.option("--translation-file", type=click.Path(exists=True), help="Path to the file containing translated lines")
def apply_translation(srt_file: Path, translation_file):
    """Apply Vietnamese translations to original SRT."""
    srt_path = Path(srt_file)
    with srt_path.open("r", encoding='utf-8') as fsub: # Added encoding
        sub_content = fsub.read()
        # Parse original subtitles using srt package
        original_subtitles = list(srt.parse(sub_content)) # Convert iterator to list to use multiple times

    with open(translation_file, "r", encoding='utf-8') as ftrans: # Added encoding
        # Assuming translation file has one translated line per original subtitle line
        translations = [line.strip() for line in ftrans if line.strip()] # Filter out empty lines

    # Use the refactored replace_sub
    new_srt_content = replace_sub(original_subtitles, translations)

    # Construct output filename (replace .en.srt with .vi.srt if applicable)
    # More robust filename replacement
    original_name = srt_path.name
    if original_name.lower().endswith('.en.srt'):
        output_name = original_name[:-7] + '.vi.srt'
    elif original_name.lower().endswith('.srt'):
         # If not specifically English, just add .vi before .srt extension
         output_name = original_name[:-4] + '.vi.srt'
    else:
         # Fallback for unexpected names
         output_name = original_name + '.vi'


    output_file = srt_path.parent / output_name
    with open(output_file, "w", encoding='utf-8') as fout: # Added encoding
        fout.write(new_srt_content)

    click.echo(f"Written translated subtitles to {output_file}")


if __name__ == "__main__":
    cli()
