"""Provayderdə hazırda əlçatan modellərin siyahısı.

    python -m src.list_models --provider google

NİYƏ AYRICA ALƏT: model adları xəbərdarlıqsız təqaüdə çıxır. `gemini-2.0-flash`
sənədlərdə hələ görünsə də, API artıq 404 qaytarır. Qaçışdan əvvəl siyahını
yoxlamaq 712 çağırışlıq qaçışın ortasında model tapılmadı xətası ilə dayanmasının
qarşısını alır.

Alət `run_eval`-dan asılı deyil və heç nə yazmır - yalnız oxuyur.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

__all__ = ["list_google", "list_anthropic", "list_openai", "main"]


def list_google(base_url: str | None = None, api_key: str | None = None) -> list[str]:
    """Mətn generasiyasını dəstəkləyən Gemini modelləri.

    DİQQƏT - klient DƏYİŞƏNDƏ saxlanılır. `genai.Client().models.list()` kimi
    yazılsa, klient müvəqqəti obyekt olur və siyahı hələ oxunarkən zibil
    toplayıcıya düşür; altındakı HTTP klienti bağlanır və ikinci səhifədə
    `RuntimeError: Cannot send a request, as the client has been closed` gəlir.
    """
    from google import genai
    from google.genai import types

    http_options = types.HttpOptions(base_url=base_url) if base_url else None
    client = genai.Client(api_key=api_key, http_options=http_options)
    return sorted(
        model.name
        for model in client.models.list()
        if "generateContent" in (model.supported_actions or [])
    )


def list_anthropic(
    base_url: str | None = None, api_key: str | None = None
) -> list[str]:
    import anthropic

    client = anthropic.Anthropic(base_url=base_url, api_key=api_key)
    return sorted(model.id for model in client.models.list())


def list_openai(base_url: str | None = None, api_key: str | None = None) -> list[str]:
    """OpenAI - və OpenAI-uyğun hər hansı katalog.

    `base_url` verilsə, NVIDIA (`integrate.api.nvidia.com`), OpenRouter, Groq,
    Together və digər endpoint-lərin model siyahısını qaytarır. Sənədləri
    oxumaqdansa katalogu API-dən soruşmaq daha etibarlıdır: cavab məhz həmin
    açarın çağıra bildiyi modelləri göstərir.
    """
    from openai import OpenAI

    client = OpenAI(base_url=base_url, api_key=api_key)
    return sorted(model.id for model in client.models.list())


_LISTERS = {
    "google": (list_google, "GOOGLE_API_KEY"),
    "anthropic": (list_anthropic, "ANTHROPIC_API_KEY"),
    "openai": (list_openai, "OPENAI_API_KEY"),
}


def probe(
    provider: str,
    names: Sequence[str],
    max_tokens: int = 8,
    detail_chars: int = 160,
    base_url: str | None = None,
    api_key: str | None = None,
) -> list[tuple]:
    """Hər modeli BİR dəfə real çağırışla sınayır.

    NİYƏ SİYAHI KİFAYƏT ETMİR: `models.list()` hesabın görə bildiyi modelləri
    qaytarır, çağıra bildiklərini yox. `gemini-2.5-flash` siyahıda görünür,
    amma yeni açarla çağırılanda `404 ... no longer available to new users`
    verir. Əlçatanlığı yalnız real çağırış təsdiqləyir.

    Çağırışlar ARDICILDIR - pulsuz səviyyələrin dəqiqəlik limiti var və paralel
    sınaq 429 verib nəticəni yanıldıcı edərdi (model işlək olduğu halda
    "uğursuz" görünərdi).
    """
    from src.backends_api import PROVIDERS

    results: list[tuple] = []
    for name in names:
        # Google adları `models/` prefiksi ilə gəlir və atılmalıdır. Üçüncü
        # tərəf kataloqlarında isə `/` adın ÖZ hissəsidir (`z-ai/glm-5.2`) -
        # kəsilsə model tapılmaz.
        model_id = name.split("/")[-1] if name.startswith("models/") else name
        try:
            adapter = PROVIDERS[provider](model_id, base_url=base_url, api_key=api_key)
            text, _, _, _ = adapter.complete("Say OK.", max_tokens)
            if not (text or "").strip():
                # Çağırış keçdi, cavab boşdur. BU, UĞUR DEYİL. Adətən səbəb
                # budur: model düşünmə rejimini söndürməyə imkan vermir və
                # `max_tokens` büdcəsini düşünməyə xərcləyib cavaba çatmır.
                # `OK` yazsaydıq, model qaçışa buraxılar və 356 sətrin hamısı
                # boş gələrdi - nəticə isə "bu model Azərbaycan dilini bilmir"
                # kimi oxunardı. Format problemi dil problemi kimi görünərdi.
                results.append((model_id, "EMPTY", "cavab boş - büdcə azdır?"))
            else:
                results.append((model_id, "OK", text[:40]))
        except Exception as exc:  # noqa: BLE001
            # Xəta mətni QISALDILMIR ki, günahkar sahənin adı görünsün.
            # 400 INVALID_ARGUMENT əlçatanlıq problemi deyil - hansı parametrin
            # rədd olunduğunu bilmədən adapteri düzəltmək mümkün deyil.
            message = str(exc)
            results.append(
                (
                    model_id,
                    type(exc).__name__,
                    message if detail_chars <= 0 else message[:detail_chars],
                )
            )
    return results


def main(argv: Sequence[str] | None = None) -> int:
    # Windows konsolu susmaya görə cp1252-dir və model adlarında ASCII-dən
    # kənar simvol olsa çökür.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="list_models", description="Provayderdə əlçatan modelləri göstərir"
    )
    parser.add_argument("--provider", choices=sorted(_LISTERS), required=True)
    parser.add_argument(
        "--base-url",
        default=None,
        help="OpenAI-uyğun üçüncü tərəf kataloqu (NVIDIA, OpenRouter, Groq...)",
    )
    parser.add_argument(
        "--api-key-env",
        default=None,
        help="açarın oxunacağı mühit dəyişəni (məs. NVIDIA_API_KEY)",
    )
    parser.add_argument(
        "--filter", default="", help="ada görə süzgəc (məs. `flash`)"
    )
    parser.add_argument(
        "--probe",
        action="store_true",
        help="hər modeli bir çağırışla sına - siyahıda görünmək çağıra bilmək demək deyil",
    )
    parser.add_argument(
        "--probe-tokens",
        type=int,
        default=8,
        help="--probe ilə: cavab büdcəsi. Boş cavab gələndə 256 ilə təkrar sına",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="--probe ilə: xəta mətnini tam göstər",
    )
    parser.add_argument(
        "--exclude",
        default="preview,image,tts,robotics,computer-use,embedding",
        help="adında bu sözlər olan modelləri at (vergüllə)",
    )
    args = parser.parse_args(argv)

    lister, default_env = _LISTERS[args.provider]
    env_var = args.api_key_env or default_env
    api_key = os.environ.get(env_var)
    if not api_key:
        print(f"{env_var} təyin olunmayıb.", file=sys.stderr)
        return 1

    try:
        names = lister(base_url=args.base_url, api_key=api_key)
    except Exception as exc:  # noqa: BLE001 - istifadəçiyə səbəbi göstərmək kifayətdir
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.filter:
        names = [n for n in names if args.filter.lower() in n.lower()]

    excluded = [word.strip().lower() for word in args.exclude.split(",") if word.strip()]
    if excluded:
        names = [n for n in names if not any(w in n.lower() for w in excluded)]

    if not args.probe:
        for name in names:
            print(name)
        print(f"\n{len(names)} model", file=sys.stderr)
        return 0

    print(
        f"{len(names)} model sınanır (ardıcıl, max_tokens={args.probe_tokens})...\n",
        file=sys.stderr,
    )
    working: list[str] = []
    empty: list[str] = []
    for model_id, status, detail in probe(
        args.provider,
        names,
        max_tokens=args.probe_tokens,
        detail_chars=0 if args.verbose else 160,
        base_url=args.base_url,
        api_key=api_key,
    ):
        if status == "OK":
            working.append(model_id)
            print(f"OK    {model_id:<40} {detail}", flush=True)
        elif status == "EMPTY":
            empty.append(model_id)
            print(f"BOŞ   {model_id:<40} {detail}", flush=True)
        else:
            print(f"yox   {model_id:<40} {status}", flush=True)
            print(f"        {detail}", flush=True)

    print(f"\nİşləyən: {len(working)}/{len(names)}", file=sys.stderr)
    if empty:
        print(
            f"Boş cavab verən: {', '.join(empty)}\n"
            f"  Bunlar çox güman düşünmə rejimini söndürməyə imkan vermir və "
            f"büdcəni düşünməyə xərcləyir.\n"
            f"  Yoxla: --probe-tokens 256 ilə təkrar sına. Cavab gəlirsə, "
            f"model işləkdir, sadəcə daha böyük büdcə istəyir.",
            file=sys.stderr,
        )
    if working:
        print(f"Qaçış üçün: --model {args.provider}:{working[-1]}", file=sys.stderr)
    return 0 if working else 1


if __name__ == "__main__":
    raise SystemExit(main())
