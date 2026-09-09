"""contamination.py üçün testlər."""

from __future__ import annotations

from src.analyze import Run, RunKey
from src.contamination import FLOOR_EN, LEAK_PROOF, build_report, gap_table


def record(record_id, answer, provenance):
    return {
        "id": record_id,
        "question_az": f"{record_id} sualı?",
        "question_en": f"{record_id} question?",
        "answer": answer,
        "answer_en": answer,
        "answer_aliases": [],
        "category": "mathematics",
        "provenance": provenance,
    }


def dataset():
    rows = {}
    for n in range(10):
        rows[f"c-{n}"] = record(f"c-{n}", f"{n}", LEAK_PROOF)
    for n in range(10):
        rows[f"m-{n}"] = record(f"m-{n}", f"m{n}", "manual")
    return rows


def run(model, language, predictions):
    return Run(
        key=RunKey(model, language),
        predictions=predictions,
        raw=dict(predictions),
    )


def test_gap_is_reported_on_the_leak_proof_subset():
    """Altdəst ayrıca ölçülür: onun sətirləri heç bir korpusda ola bilməz."""
    ds = dataset()
    ids = [i for i, r in ds.items() if r["provenance"] == LEAK_PROOF]
    runs = {
        ("m", "en"): run("m", "en", {i: ds[i]["answer"] for i in ids}),
        ("m", "az"): run("m", "az", {i: "yanlış" for i in ids}),
    }
    table = gap_table(ds, runs, ids)
    assert "100.0%" in table and "0.0%" in table
    assert "100.0pp" in table


def test_floor_models_are_marked_not_silently_counted():
    """Hər iki dildə sıfır alan modelin 0.0 fərqi 'uçurum yoxdur' demək deyil.

    İşarələnməsəydi, cədvəldəki sıfır oxucuya dəlil kimi görünərdi, halbuki
    həmin model tapşırığı ümumiyyətlə bacarmır.
    """
    ds = dataset()
    ids = [i for i, r in ds.items() if r["provenance"] == LEAK_PROOF]
    runs = {
        ("floor", "en"): run("floor", "en", {i: "yanlış" for i in ids}),
        ("floor", "az"): run("floor", "az", {i: "yanlış" for i in ids}),
    }
    table = gap_table(ds, runs, ids)
    assert "*" in table
    assert "itirəcək balları yoxdur" in table


def test_capable_model_is_not_marked_as_floor():
    ds = dataset()
    ids = [i for i, r in ds.items() if r["provenance"] == LEAK_PROOF]
    runs = {
        ("good", "en"): run("good", "en", {i: ds[i]["answer"] for i in ids}),
        ("good", "az"): run("good", "az", {i: ds[i]["answer"] for i in ids}),
    }
    table = gap_table(ds, runs, ids)
    assert "itirəcək balları yoxdur" not in table


def test_floor_threshold_is_low_enough_to_mean_incapable():
    """Hədd 'zəif' yox, 'bacarmır' deməlidir."""
    assert 0 < FLOOR_EN <= 0.10


def test_report_states_the_exact_claim():
    """Hesabat sətir sızması ilə fakt biliyini QARIŞDIRMAMALIDIR.

    "Bu faktlar korpusda yoxdur" iddiası yanlış olardı və lazım da deyil:
    ölçülən şey elə həmin biliyin azərbaycanca işlədilə bilməsidir.
    """
    ds = dataset()
    ids = [i for i, r in ds.items() if r["provenance"] == LEAK_PROOF]
    runs = {
        ("m", "en"): run("m", "en", {i: ds[i]["answer"] for i in ids}),
        ("m", "az"): run("m", "az", {i: "yanlış" for i in ids}),
    }
    report = build_report(ds, runs)
    assert "SƏTİRLƏR sızmayıb" in report
    assert "FAKTLARIN" in report


def test_report_refuses_to_call_provenance_a_proof():
    """Mənşə müqayisəsi çətinlik fərqi ilə qarışır və dəlil sayıla bilməz."""
    ds = dataset()
    ids = list(ds)
    runs = {
        ("m", "en"): run("m", "en", {i: ds[i]["answer"] for i in ids}),
        ("m", "az"): run("m", "az", {i: "yanlış" for i in ids}),
    }
    report = build_report(ds, runs)
    assert "dəlil deyil" in report
    assert "sitelinks" in report
