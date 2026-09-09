"""Bütün qaçışları ardıcıl icra edir və hər birinin nəticəsini ayrıca bildirir.

Resume defolt açıqdır, ona görə yalnız çatışmayan sətirlər hesablanır.
Bir qaçış uğursuz olsa, qalanları DAYANDIRILMIR — hansının alınmadığı sonda
xülasədə görünür, beləcə bir model çökəndə bütün gecə itmir.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# (model, dil, üslub, əlavə bayraqlar)
# 4-bit yalnız 4B+ üçün — 8 GB VRAM-a fp16-da sığmır.
RUNS = [
    ("Qwen/Qwen3-1.7B", "az", "default", []),
    ("Qwen/Qwen3-1.7B", "en", "default", []),
    ("Qwen/Qwen3-VL-4B-Instruct", "az", "default", ["--load-in-4bit"]),
    ("Qwen/Qwen3-VL-4B-Instruct", "en", "default", ["--load-in-4bit"]),
    # Qoldanın ELAN ETDİYİ baza modeli. Müqayisənin əsas nöqtəsidir, ona görə
    # siyahıda olmalıdır; əvvəl əl ilə qaçırılırdı və siyahıdan kənarda idi.
    ("Qwen/Qwen3-VL-4B-Thinking", "az", "default", ["--load-in-4bit"]),
    ("Qwen/Qwen3-VL-4B-Thinking", "en", "default", ["--load-in-4bit"]),
    ("issai/Qolda-AVL-5B", "az", "default", ["--load-in-4bit", "--trust-remote-code"]),
    ("issai/Qolda-AVL-5B", "en", "default", ["--load-in-4bit", "--trust-remote-code"]),
    ("issai/Qolda-AVL-5B", "az", "script", ["--load-in-4bit", "--trust-remote-code"]),
    ("issai/Qolda-AVL-5B", "en", "script", ["--load-in-4bit", "--trust-remote-code"]),
    # İKİNCİ FINE-TUNE CÜTÜ. Əsas iddia ("qazax dilinə köklənmə azərbaycanca
    # yazını pozur") tək Qolda üzərində qurulsaydı, o, bir modelin
    # özünəməxsusluğu ola bilərdi. Bu cüt eyni sualı ikinci dəfə verir:
    # `Qwen3.5-4B-Base` və onun qazax variantı, hər ikisi ISSAI-dən.
    ("Qwen/Qwen3.5-4B-Base", "az", "default", ["--load-in-4bit"]),
    ("Qwen/Qwen3.5-4B-Base", "en", "default", ["--load-in-4bit"]),
    ("issai/Qwen3.5-4B-Base-Kazakh", "az", "default", ["--load-in-4bit"]),
    ("issai/Qwen3.5-4B-Base-Kazakh", "en", "default", ["--load-in-4bit"]),
    # QEYRİ-QWEN AİLƏLƏRİ. Yuxarıdakı hər model Qwen-dəndir (Qolda və qazax
    # variantı da Qwen-dən köklənib), ona görə bütün nəticələr Qwen-in
    # xüsusiyyəti ola bilərdi. Bunlar həmin etirazı bağlayır.
    ("microsoft/Phi-3.5-mini-instruct", "az", "default", ["--load-in-4bit"]),
    ("microsoft/Phi-3.5-mini-instruct", "en", "default", ["--load-in-4bit"]),
    ("tiiuae/Falcon3-3B-Instruct", "az", "default", ["--load-in-4bit"]),
    ("tiiuae/Falcon3-3B-Instruct", "en", "default", ["--load-in-4bit"]),
]

#: Ailə əhatəsini genişləndirən modellər. Ayrı siyahıda saxlanılır, çünki
#: yuxarıdakılar əsas nəticələri istehsal edir və HƏMİŞƏ qaçırılmalıdır;
#: bunlar isə yerli keşdə olmaya bilər və uğursuzluqları planlıdır.
#:
#: Üç qrupa bölünür:
#:   müstəqil ailələr   "hər şey Qwen-dir" etirazını bağlayır
#:   azərbaycanca əhatə  dil etiketində `az` olan modellər
#:   TÜRK CÜTÜ          qazax cütlərinin latın əlifbalı analoqu
EXTRA = [
    # Müstəqil ailələr
    ("mistralai/Mistral-7B-Instruct-v0.3", ["--load-in-4bit"]),
    ("ibm-granite/granite-3.1-2b-instruct", ["--load-in-4bit"]),
    ("bigscience/bloomz-1b7", ["--load-in-4bit"]),
    ("allenai/OLMo-2-1124-7B-Instruct", ["--load-in-4bit"]),
    ("microsoft/Phi-4-mini-instruct", ["--load-in-4bit"]),
    ("HuggingFaceTB/SmolLM2-1.7B-Instruct", ["--load-in-4bit"]),
    ("stabilityai/stablelm-2-1_6b-chat", ["--load-in-4bit"]),
    ("01-ai/Yi-1.5-6B-Chat", ["--load-in-4bit"]),
    # Azərbaycan dilini açıq şəkildə əhatə edən modellər
    ("ai-forever/mGPT", ["--load-in-4bit"]),
    ("thelamapi/next-1b", ["--load-in-4bit", "--trust-remote-code"]),
    ("utter-project/EuroLLM-1.7B-Instruct", ["--load-in-4bit"]),
    ("ATH-MaaS/Marco-Nano-Instruct", ["--load-in-4bit", "--trust-remote-code"]),
    # Birinci türk cütü: qohum dil, amma LATIN əlifba. Qazax cütləri ilə
    # birlikdə "qohum dilə köklənmə" amilini "yazı sistemi" amilindən ayırır.
    ("mistralai/Mistral-7B-v0.1", ["--load-in-4bit"]),
    ("Trendyol/Trendyol-LLM-7b-base-v1.0", ["--load-in-4bit"]),
    # İKİNCİ türk cütü. Birincisi tək qalsaydı, "latın köklənmə zərər vermir"
    # iddiası bir ölçmədən asılı olardı; həmin ölçmə də `Trendyol`-un aşağı
    # mütləq balı ilə yüklüdür. Bu cüt ayrı baza ailəsindən (Llama-3) və ayrı
    # komandadandır.
    #
    # `--no-chat-template` HƏR İKİSİNƏ verilir. Üçüncü cütdə nəticəni sıfıra
    # endirən səhv məhz asimmetriya idi: fine-tune olunmuş model şablonla,
    # baza modeli şablonsuz soruşulmuşdu. Burada heç birində şablon yoxdur,
    # yəni bayraq artıq görünür, amma asimmetriyanın təsadüfən qayıtmasının
    # qarşısını alır.
    ("meta-llama/Meta-Llama-3-8B", ["--load-in-4bit", "--no-chat-template"]),
    (
        "ytu-ce-cosmos/Turkish-Llama-8b-v0.1",
        ["--load-in-4bit", "--no-chat-template"],
    ),
    # Müstəqil ailələr, ikinci dalğa: "hər şey Qwen-dir" etirazını bağlayır.
    # Google, Cohere. Gemma multimodal `gemma3` tipindədir və
    # `AutoModelForCausalLM` ilə yüklənmir; `run_eval` geri dönüş zənciri
    # bunu özü həll edir.
    ("google/gemma-3-4b-it", ["--load-in-4bit"]),
    ("CohereLabs/aya-expanse-8b", ["--load-in-4bit"]),
]

RUNS += [(m, lang, "default", flags) for m, flags in EXTRA for lang in ("az", "en")]


def main() -> int:
    # Windows konsolu susmaya görə cp1252-dir və çıxış boruya yönləndiriləndə
    # UTF-8-ə keçmir. Aşağıdakı xülasə sətrində "dəq" sözü var; `ə` (U+0259)
    # cp1252-də yoxdur və proqram MƏHZ ORADA çökür.
    #
    # Bu, ucuz səhv deyil: səkkiz qaçışın birincisi bitəndən sonra baş verir,
    # yəni bir model hesablanır, qalan yeddisi ümumiyyətlə başlamır. `run_eval`
    # bu qorumanı özündə saxlayır; burada da olmalıdır.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    results: list[tuple[str, int, float]] = []

    for index, (model, language, style, extra) in enumerate(RUNS, start=1):
        label = f"{model} [{language}/{style}]"
        cmd = [
            sys.executable, "-m", "src.run_eval",
            "--model", model,
            "--language", language,
            "--prompt-style", style,
            "--max-new-tokens", "32",
            "--batch-size", "8",
            "--seed", "0",
            *extra,
        ]
        print(f"\n{'=' * 72}\n[{index}/{len(RUNS)}] {label}\n{'=' * 72}", flush=True)

        started = time.time()
        completed = subprocess.run(cmd, cwd=ROOT)
        elapsed = time.time() - started

        results.append((label, completed.returncode, elapsed))
        state = "OK" if completed.returncode == 0 else f"XƏTA ({completed.returncode})"
        print(f"\n--> {state}  {elapsed / 60:.1f} dəq  {label}", flush=True)

    print(f"\n{'=' * 72}\nXÜLASƏ\n{'=' * 72}", flush=True)
    for label, code, elapsed in results:
        state = "OK  " if code == 0 else "XƏTA"
        print(f"  {state}  {elapsed / 60:6.1f} dəq  {label}", flush=True)

    failed = sum(1 for _, code, _ in results if code != 0)
    print(f"\n{len(results) - failed}/{len(results)} uğurlu", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
