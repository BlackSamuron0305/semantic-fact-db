"""Tests for synthetic dataset generation."""

from sfdb.datasets.synthetic import SyntheticConfig, generate_facts, generate_random_graph


class TestSyntheticConfig:
    def test_default_config(self) -> None:
        config = SyntheticConfig()
        assert config.num_entities == 100
        assert config.num_facts == 1000

    def test_distribution_validation(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            SyntheticConfig(max_arity=3, arity_distribution=(0.5, 0.5))  # wrong length
        with pytest.raises(ValueError):
            SyntheticConfig(max_arity=2, arity_distribution=(0.8, 0.3))  # sums to 1.1


class TestGenerateFacts:
    def test_basic_generation(self) -> None:
        config = SyntheticConfig(num_entities=10, num_facts=50, seed=42)
        dataset = generate_facts(config)
        assert dataset.num_facts == 50
        assert dataset.num_entities == 10
        assert dataset.num_relations == 10

    def test_reproducibility(self) -> None:
        config = SyntheticConfig(num_entities=10, num_facts=50, seed=42)
        dataset1 = generate_facts(config)
        dataset2 = generate_facts(config)
        assert len(dataset1.facts) == len(dataset2.facts)
        for f1, f2 in zip(dataset1.facts, dataset2.facts, strict=False):
            assert f1.subject == f2.subject
            assert f1.relation == f2.relation

    def test_arity_distribution(self) -> None:
        config = SyntheticConfig(
            num_entities=10,
            num_facts=100,
            min_arity=1,
            max_arity=3,
            arity_distribution=(0.0, 0.5, 0.5),  # Only arity 2 and 3
            seed=42,
        )
        dataset = generate_facts(config)
        for fact in dataset.facts:
            assert fact.arity() in (2, 3)


class TestGenerateRandomGraph:
    def test_graph_generation(self) -> None:
        facts = generate_random_graph(num_nodes=20, edge_density=0.3, seed=42)
        assert len(facts) > 0
        for fact in facts:
            assert fact.relation.value == "connected_to"

    def test_reproducibility(self) -> None:
        f1 = generate_random_graph(num_nodes=10, edge_density=0.5, seed=42)
        f2 = generate_random_graph(num_nodes=10, edge_density=0.5, seed=42)
        assert len(f1) == len(f2)
