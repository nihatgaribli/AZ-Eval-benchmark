"""Bütün qaçışları 1005 sətirlik datasetə uzadır.

    python run_extend_1005.py --list        # mərhələləri gör
    python run_extend_1005.py --stage a     # bir mərhələ
    python run_extend_1005.py               # hamısı, ~3 saat

HİSSƏ-HİSSƏ QAÇIRILA BİLƏR. Mərhələlər elə bölünüb ki, hər birindən sonra
layihə İŞLƏK vəziyyətdə qalsın və nəyisə yenidən qurmaq mümkün olsun.
Mərhələ təsviri üçün `STAGES` sözlüyünə bax.

YARIMÇIQ KƏSMƏK TƏHLÜKƏSİZDİR. `run_eval` hər cavabı dərhal fayla yazır və
növbəti dəfə qaldığı yerdən davam edir, ona görə Ctrl+C ilə dayandırmaq heç
nə itirmir.

SIRA ƏHƏMİYYƏTLİDİR. `a` mərhələsinin faylları SIFIRDAN yazılır (şablon
düzəlişi zamanı kənara qoyulublar), qalan mərhələlər isə mövcud fayla ƏLAVƏ
edir. Sıra tərs olsaydı, düzəldilməmiş fayl uzadılar və içində iki fərqli
şərait qarışardı.

ŞABLON BAYRAQLARI. `--no-chat-template` yalnız cütü simmetrik saxlamaq üçün
verilir, ümumi qayda kimi yox. Səbəb və ölçülmüş təsir:
`results/raw_outputs/invalid_chat_template/README.md`.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

#: Model başına bayraqlar. `--no-chat-template` YALNIZ cütü simmetrik saxlamaq
#: üçün verilir, ümumi qayda kimi yox.
FLAGS: dict[str, list[str]] = {
    "issai/Qolda-AVL-5B": ["--load-in-4bit", "--trust-remote-code"],
    "thelamapi/next-1b": ["--load-in-4bit", "--trust-remote-code"],
    "meta-llama/Meta-Llama-3-8B": ["--load-in-4bit", "--no-chat-template"],
    "ytu-ce-cosmos/Turkish-Llama-8b-v0.1": ["--load-in-4bit", "--no-chat-template"],
    "Trendyol/Trendyol-LLM-7b-base-v1.0": ["--load-in-4bit", "--no-chat-template"],
    "Qwen/Qwen3-VL-4B-Thinking": ["--load-in-4bit", "--no-chat-template"],
    "Qwen/Qwen3.5-4B-Base": ["--load-in-4bit", "--no-chat-template"],
}
DEFAULT_FLAGS = ["--load-in-4bit"]

#: Elan edilmiş cütlərin modelləri. Bunlar birinci qaçır.
PAIR_MODELS = [
    "Qwen/Qwen3-VL-4B-Thinking",
    "issai/Qolda-AVL-5B",
    "Qwen/Qwen3.5-4B-Base",
    "issai/Qwen3.5-4B-Base-Kazakh",
    "mistralai/Mistral-7B-v0.1",
    "Trendyol/Trendyol-LLM-7b-base-v1.0",
    "meta-llama/Meta-Llama-3-8B",
    "ytu-ce-cosmos/Turkish-Llama-8b-v0.1",
]

OTHER_MODELS = [
    "Qwen/Qwen3-VL-4B-Instruct",
    "google/gemma-3-4b-it",
    "CohereLabs/aya-expanse-8b",
    "microsoft/Phi-4-mini-instruct",
    "microsoft/Phi-3.5-mini-instruct",
    "Qwen/Qwen3-1.7B",
    "tiiuae/Falcon3-3B-Instruct",
    "ibm-granite/granite-3.1-2b-instruct",
    "ai-forever/mGPT",
    "thelamapi/next-1b",
    "HuggingFaceTB/SmolLM2-1.7B-Instruct",
    "stabilityai/stablelm-2-1_6b-chat",
    "utter-project/EuroLLM-1.7B-Instruct",
    "bigscience/bloomz-1b7",
]

#: Möhkəmlik yoxlaması üçün üslub qaçışları. `Qwen3-VL-4B-Thinking` burada da
#: şablonsuz qaçır: cüt fərqi məhz bu modellə hesablanır və möhkəmlik
#: yoxlamasının özündə artefakt olması onun mənasını yox edərdi.
STYLE_RUNS = [
    (model, style)
    for style in ("zeroshot", "plain")
    for model in (
        "Qwen/Qwen3-VL-4B-Thinking",
        "issai/Qolda-AVL-5B",
        "Qwen/Qwen3-VL-4B-Instruct",
    )
]


#: MƏRHƏLƏLƏR. Bölgü təsadüfi deyil: hər mərhələdən sonra layihə İŞLƏK
#: vəziyyətdə qalır və nəyisə yenidən qurmaq mümkün olur.
#:
#:   a  Thinking modelinin üslub qaçışlarının bərpası. BLOKLAYICIDIR: həmin
#:      fayllar hazırda ümumiyyətlə yoxdur (şablon düzəlişi zamanı kənara
#:      qoyuldu), yəni `prompts.md` bu mərhələsiz qurula bilmir.
#:   b  Elan edilmiş cütlərin modelləri. Bundan sonra `pairs.md` tam 1005
#:      sual üzərində qurula bilir, yəni ƏSAS NƏTİCƏ hazır olur.
#:   c  Qalan üslub qaçışları. Bundan sonra `prompts.md` qurula bilir.
#:   d  Genişlik üçün əlavə edilmiş 14 model.
#:
#: ÖRTÜK QAPISI HAQQINDA XƏBƏRDARLIQ. `analyze.py` datasetin 90%-dən azını
#: örtən qaçışı müqayisə cədvəllərinə salmır. 729/1005 = 72.5%, yəni
#: uzadılmamış model həmin cədvəllərdən DÜŞÜR. Ona görə `d` bitənə qədər
#: əsas sıralama cədvəlləri natamam olacaq. Bu, qüsur deyil, qapının işidir.
STAGES: dict[str, str] = {
    "a": "Thinking üslub qaçışlarının bərpası (şablonsuz, tam 1005 sətir)",
    "b": "Elan edilmiş cütlərin modelləri -> `pairs.md` hazır olur",
    "c": "Qalan üslub qaçışları -> `prompts.md` hazır olur",
    "d": "Genişlik üçün 14 model -> əsas cədvəllər tam olur",
}


def jobs(stage: str = "all") -> list[tuple[str, str, str]]:
    """Seçilmiş mərhələnin qaçışları.

    `a` mərhələsi `b`-dən ƏVVƏL gəlməlidir: onun faylları sıfırdan yazılır,
    uzatma isə mövcud fayla əlavə edir. Sıra tərs olsaydı, düzəldilməmiş
    fayl uzadılar və içində iki fərqli şərait qarışardı.
    """
    thinking = "Qwen/Qwen3-VL-4B-Thinking"
    by_stage: dict[str, list[tuple[str, str, str]]] = {
        "a": [
            (thinking, lang, style)
            for style in ("zeroshot", "plain")
            for lang in ("az", "en")
        ],
        "b": [(m, lang, "default") for m in PAIR_MODELS for lang in ("az", "en")],
        "c": [
            (m, lang, st)
            for m, st in STYLE_RUNS
            if m != thinking
            for lang in ("az", "en")
        ],
        "d": [(m, lang, "default") for m in OTHER_MODELS for lang in ("az", "en")],
    }
    if stage == "all":
        return [job for key in ("a", "b", "c", "d") for job in by_stage[key]]
    if stage not in by_stage:
        raise SystemExit(f"tanınmayan mərhələ: {stage}. Mümkün: {sorted(by_stage)}, all")
    return by_stage[stage]


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="run_extend_1005")
    parser.add_argument(
        "--stage",
        default="all",
        help="a | b | c | d | all. `--list` ilə mərhələləri gör.",
    )
    parser.add_argument(
        "--list", action="store_true", help="mərhələləri sadala və çıx"
    )
    args = parser.parse_args()

    if args.list:
        for key, description in STAGES.items():
            print(f"  {key}  {len(jobs(key)):2} qaçış   {description}")
        return 0

    todo = jobs(args.stage)
    print(f"Mərhələ `{args.stage}`: {len(todo)} qaçış")
    results = []
    for index, (model, language, style) in enumerate(todo, start=1):
        label = f"{model} [{language}/{style}]"
        print(f"\n{'=' * 72}\n[{index}/{len(todo)}] {label}\n{'=' * 72}", flush=True)
        started = time.time()
        completed = subprocess.run(
            [
                sys.executable, "-m", "src.run_eval",
                "--model", model,
                "--language", language,
                "--prompt-style", style,
                "--max-new-tokens", "32",
                "--batch-size", "8",
                "--seed", "0",
                *FLAGS.get(model, DEFAULT_FLAGS),
            ],
            cwd=ROOT,
        )
        results.append((label, completed.returncode, time.time() - started))

    print(f"\n{'=' * 72}\nXÜLASƏ\n{'=' * 72}")
    failed = 0
    for label, code, elapsed in results:
        if code != 0:
            failed += 1
        print(f"  {'OK ' if code == 0 else 'XTA'} {label:56} {elapsed / 60:5.1f} deq")
    print(f"\n{len(results) - failed}/{len(results)} uğurlu")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
