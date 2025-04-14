import re
from typing import List
from pathlib import Path

import click


def replace_sub(text: str, replacements: List[str]) -> str:
    assert len(replacements) *4  == text.count("\n"), f'num lines of translation({len(replacements) * 4}) and sub({text.count("\n")}) must equal'

    PATTERN = re.compile(
        r"\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n(.*)?\n",
        re.MULTILINE,
    )

    def replacer(match):
        if replacements:
            return match.group(0).replace(match.group(1), replacements.pop(0))
        return match.group(0)

    return PATTERN.sub(replacer, text)


def extract_content(subtitle: str) -> List[str]:
    PATTERN = re.compile(
        r"\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n(.*)\n",
        re.MULTILINE,
    )
    matches = re.finditer(PATTERN, subtitle)
    return [match.group(1) for match in matches if match.groups()]


def is_end_sentence(text: str) -> bool:
    return re.search(r"\w[.!?]$", text) is not None


def split(content: List[str], limit: int = 10) -> List[List[str]]:
    start_idx = 0
    end_idx = 0
    idx = 0
    parts = []

    while idx <= len(content) - 1:
        if len(content[start_idx : idx + 1]) == limit:
            for i in range(idx, start_idx - 1, -1):
                if is_end_sentence(content[i]):
                    end_idx = i
                    break
            else:
                end_idx = idx - 1

            parts.append(content[start_idx : end_idx + 1])
            start_idx = end_idx + 1
        idx += 1

    parts.append(content[start_idx:])
    return parts


def gen_prompt(content: str) -> str:
    return (
        "The following paragraph is the transcript (from srt file) of the MIT Supply "
        'Chain Fundamentals lecture, translate it into Vietnamese, do not remove "|" characters, '
        'It is used to separate subtitles: \n"{content}"'
    ).replace("{content}", content)


@click.group()
def cli():
    """Subtitle Processing CLI"""
    pass


@cli.command()
@click.option("--srt-file", type=click.Path(exists=True))
@click.option("--limit", default=70, help="Limit per chunk")
@click.option("--output-dir", default=".", help="Directory to write prompt files")
def gen_prompts(srt_file: Path, limit, output_dir):
    """Generate translation prompts from SRT file"""
    srt_path = Path(srt_file)
    with srt_path.open("r") as f:
        sub = f.read()
        parts = split(extract_content(sub), limit=limit)

        for i, content in enumerate(parts):
            out_path = Path(output_dir) / f"prompt{i}.txt"
            with out_path.open("w") as f_out:
                f_out.write(gen_prompt("|".join(content)))

    click.echo(
        f"Generated {len(parts)} prompt files in {output_dir}, please use llm to translate this and paste into a txt file!"
    )


@cli.command()
@click.option("--srt-file", type=click.Path(exists=True))
@click.option("--translation-file", type=click.Path(exists=True))
def apply_translation(srt_file: Path, translation_file):
    """Apply Vietnamese translations to original SRT"""
    with open(srt_file, "r") as fsub:
        sub = fsub.read()

    with open(translation_file, "r") as ftrans:
        trans = [line.strip() for line in ftrans]

    new_srt = replace_sub(sub, trans)

    output_file = Path(srt_file).parent / Path(Path(srt_file).name.replace("en", "vi"))
    with open(output_file, "w") as fout:
        fout.write(new_srt)

    click.echo(f"Written translated subtitles to {output_file}")


if __name__ == "__main__":
    cli()
