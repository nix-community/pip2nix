import pytest

from pip2nix.dependencies import resolve_dependencies
from pip2nix.errors import ReportError


ENVIRONMENT = {"python_version": "3.13", "sys_platform": "linux"}


def entry(name, version="1.0", requires=(), requested_extras=()):
    return {
        "requested_extras": list(requested_extras),
        "metadata": {
            "name": name,
            "version": version,
            "requires_dist": list(requires),
        },
    }


def resolve(*entries, environment=ENVIRONMENT):
    return resolve_dependencies(list(entries), environment)


def test_reads_an_edge_from_a_declared_requirement():
    graph = resolve(
        entry("requests", requires=["idna<4,>=2.5"]), entry("idna", version="3.18")
    )

    assert graph["requests"] == [("idna", "3.18")]


def test_drops_a_requirement_the_resolution_does_not_contain():
    graph = resolve(entry("requests", requires=["idna<4,>=2.5"]))

    assert graph["requests"] == []


def test_matches_a_name_across_separators_and_case():
    graph = resolve(
        entry("requests", requires=["Charset_Normalizer<4"]),
        entry("charset-normalizer"),
    )

    assert graph["requests"] == [("charset-normalizer", "1.0")]


def test_drops_a_requirement_its_marker_excludes():
    graph = resolve(
        entry("genshi", requires=['importlib-resources; python_version<"3.9"']),
        entry("importlib-resources"),
    )

    assert graph["genshi"] == []


def test_evaluates_markers_against_the_reports_environment():
    graph = resolve(
        entry("genshi", requires=['importlib-resources; python_version<"3.9"']),
        entry("importlib-resources"),
        environment={"python_version": "3.8"},
    )

    assert graph["genshi"] == [("importlib-resources", "1.0")]


def test_does_not_infer_an_edge_from_an_inactive_extra():
    graph = resolve(
        entry("pluggy", requires=['pytest>=1; extra=="dev"']),
        entry("pytest", requires=["pluggy<2,>=1.5"]),
    )

    assert graph["pluggy"] == []
    assert graph["pytest"] == [("pluggy", "1.0")]


def test_reads_an_edge_the_extra_of_a_dependent_activates():
    graph = resolve(
        entry("trytond", requires=["relatorio[fodt]>=0.7.0"]),
        entry("relatorio", requires=['puremagic; extra=="fodt"']),
        entry("puremagic"),
    )

    assert graph["relatorio"] == [("puremagic", "1.0")]


def test_reads_an_edge_the_extra_the_user_asked_for_activates():
    graph = resolve(
        entry(
            "relatorio",
            requested_extras=["fodt"],
            requires=['puremagic; extra=="fodt"'],
        ),
        entry("puremagic"),
    )

    assert graph["relatorio"] == [("puremagic", "1.0")]


def test_carries_an_extra_along_the_edges_it_activates():
    graph = resolve(
        entry("trytond", requires=["relatorio[fodt]"]),
        entry("relatorio", requires=['puremagic[svg]; extra=="fodt"']),
        entry("puremagic", requires=['cairosvg; extra=="svg"']),
        entry("cairosvg"),
    )

    assert graph["puremagic"] == [("cairosvg", "1.0")]


def test_reports_a_requirement_it_cannot_read():
    with pytest.raises(ReportError) as error:
        resolve(entry("trytond", requires=["not a requirement!"]))

    assert "trytond" in str(error.value)
    assert "not a requirement!" in str(error.value)
