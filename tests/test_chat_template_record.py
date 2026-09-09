"""Chat şablonunun vəziyyəti sətirlərə YAZILMALIDIR.

NİYƏ AYRI TEST FAYLI. Bu, kosmetik metadata deyil, AUDİT vasitəsidir.
Şablonun tətbiq olunub-olunmadığı çıxış faylından görünmürdü, çünki `prompt`
sahəsi şablondan əvvəlki mətni saxlayır. Nəticədə cüt daxilindəki asimmetriya
(baza modelində şablon var, köklənmişdə yox) fayllara baxaraq tapıla bilmirdi
və layihədə eyni səhv İKİ DƏFƏ baş verdi.

Testlər `describe()` məntiqini yoxlayır. Obyekt `__init__`-siz qurulur, çünki
əsl konstruktor `torch` və `transformers` tələb edir və modeli yaddaşa yükləyir.
"""

from __future__ import annotations

from src.run_eval import TransformersBackend


class FakeTokenizer:
    def __init__(self, chat_template=None):
        self.chat_template = chat_template


def backend(*, requested: bool, template) -> TransformersBackend:
    """Konstruktoru işə salmadan yalnız `describe()` üçün lazım olan hal."""
    instance = object.__new__(TransformersBackend)
    instance.use_chat_template = requested
    instance.tokenizer = FakeTokenizer(template)
    return instance


def test_template_applied_when_requested_and_available():
    meta = backend(requested=True, template="{{ messages }}").describe()
    assert meta["chat_template_requested"] is True
    assert meta["chat_template_available"] is True
    assert meta["chat_template_applied"] is True


def test_template_not_applied_when_the_model_has_none():
    """Baza modelində şablon yoxdur: xam prompt gedir.

    Məhz bu hal cütün digər yarısı ilə fərqlənəndə asimmetriya yaranır.
    """
    meta = backend(requested=True, template=None).describe()
    assert meta["chat_template_requested"] is True
    assert meta["chat_template_available"] is False
    assert meta["chat_template_applied"] is False


def test_template_not_applied_when_explicitly_turned_off():
    """`--no-chat-template` ilə şablon olsa da tətbiq olunmur."""
    meta = backend(requested=False, template="{{ messages }}").describe()
    assert meta["chat_template_requested"] is False
    assert meta["chat_template_available"] is True
    assert meta["chat_template_applied"] is False


def test_requested_and_available_are_separate_fields():
    """İki sahə birləşdirilə bilməz: səbəb fərqlidir, düzəliş də fərqlidir.

    Şablon YOXDURSA, cütü simmetrikləşdirmək üçün digər yarıya da
    `--no-chat-template` verilir. İstifadəçi şablonu İSTƏMƏYİBSƏ, bu, artıq
    edilmiş qərardır. Tək bayraq bu iki halı ayırd etməzdi.
    """
    off_because_missing = backend(requested=True, template=None).describe()
    off_because_asked = backend(requested=False, template="x").describe()

    assert off_because_missing["chat_template_applied"] is False
    assert off_because_asked["chat_template_applied"] is False
    assert off_because_missing != off_because_asked


def test_an_asymmetric_pair_is_detectable_from_the_records():
    """İki qaçışın metadatası yan-yana qoyulanda asimmetriya GÖRÜNMƏLİDİR.

    Testin özü budur: qeyd elə olmalıdır ki, cütün iki yarısının eyni şəraitdə
    soruşulub-soruşulmadığı sonradan yoxlana bilsin.
    """
    base = backend(requested=True, template="{{ messages }}").describe()
    tuned = backend(requested=True, template=None).describe()

    assert base["chat_template_applied"] != tuned["chat_template_applied"]

    # Düzəlişdən sonra simmetrik olur.
    fixed_base = backend(requested=False, template="{{ messages }}").describe()
    assert fixed_base["chat_template_applied"] == tuned["chat_template_applied"]


# --------------------------------------------------------------------------
# Model revizyonu: təkrarlanma üçün yazılır, tapılmasa qaçış dayanmır
# --------------------------------------------------------------------------


class FakeConfig:
    def __init__(self, commit_hash):
        self._commit_hash = commit_hash


def test_revision_is_recorded_when_available():
    """HuggingFace çəkiləri dəyişə bilir; hash olmadan qaçış təkrarlanmır."""
    instance = backend(requested=True, template="{{ messages }}")
    instance.model = type("M", (), {"config": FakeConfig("abc123")})()
    assert instance.describe()["model_revision"] == "abc123"


def test_describe_survives_without_a_loaded_model():
    """`describe()` model yüklənmədən də çağırıla bilir.

    Bu test bir regressiyanı kilidləyir: revizyon oxunuşu `self.model`-a
    birbaşa müraciət edəndə şablon testləri `AttributeError` ilə sınırdı.
    Metadata sahəsinin olmaması ölçməni dayandırmamalıdır.
    """
    meta = backend(requested=True, template="{{ messages }}").describe()
    assert meta["model_revision"] is None
    assert meta["chat_template_applied"] is True


def test_revision_falls_back_to_tokenizer_metadata():
    instance = backend(requested=False, template=None)
    instance.tokenizer.init_kwargs = {"_commit_hash": "def456"}
    assert instance.describe()["model_revision"] == "def456"
