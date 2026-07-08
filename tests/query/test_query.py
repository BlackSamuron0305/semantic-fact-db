"""Tests for query engine modules matching actual codebase APIs."""

import pytest

from common.interfaces import EngineType
from sfdb.common.types import Value
from sfdb.query.ast import (
    BinaryOp,
    BinaryOpNode,
    ComparisonNode,
    FunctionCallNode,
    IdentifierNode,
    LiteralNode,
    NodeType,
    OrderDirection,
    OrderNode,
    SelectNode,
    VariableNode,
)
from sfdb.query.ast import (
    LimitNode as ASTLimitNode,
)
from sfdb.query.benchmark import BenchmarkCollector, BenchmarkEntry
from sfdb.query.cache import LRUCache, QueryCache
from sfdb.query.canonical import CanonicalColumn, CanonicalResult, CanonicalRow
from sfdb.query.errors import LexerError
from sfdb.query.execution import QueryExecutionEngine
from sfdb.query.lexer import Lexer, Token, TokenType
from sfdb.query.logical_plan import (
    AggregateNode,
    FilterNode,
    JoinNode,
    LimitNode,
    LogicalOperatorType,
    LogicalPlan,
    LogicalPlanBuilder,
    ProjectionNode,
    ScanNode,
    SelectionNode,
    SortNode,
    TemporalFilterNode,
    logical_plan_to_text,
)
from sfdb.query.optimizer import (
    ConstantFolding,
    CostModel,
    DeadOperatorRemoval,
    LogicalSimplification,
    QueryOptimizer,
)
from sfdb.query.physical_plans import (
    KGPhysicalPlanBuilder,
    PhysicalOperatorType,
    PhysicalPlan,
    PhysicalPlanNode,
    SheafPhysicalPlanBuilder,
    physical_plan_to_text,
)
from sfdb.query.statistics import StatisticsStore, TableStatistics

# =====================================================================
# Lexer
# =====================================================================


class TestLexer:
    def test_simple_select(self):
        tokens = Lexer("SELECT ?s ?p ?o WHERE { ?s ?p ?o }").tokenize()
        types = [t.type for t in tokens]
        assert TokenType.SELECT in types
        assert TokenType.WHERE in types
        assert TokenType.LBRACE in types
        assert TokenType.RBRACE in types

    def test_variables(self):
        tokens = Lexer("?x ?name").tokenize()
        vars = [t for t in tokens if t.type == TokenType.VARIABLE]
        assert len(vars) == 2
        assert vars[0].value == "x"  # stored without ?

    def test_strings(self):
        tokens = Lexer('"hello" "world"').tokenize()
        strs = [t for t in tokens if t.type == TokenType.STRING]
        assert len(strs) == 2
        assert strs[0].value == "hello"

    def test_numbers(self):
        tokens = Lexer("42 3.14").tokenize()
        nums = [t for t in tokens if t.type == TokenType.NUMBER]
        assert len(nums) == 2

    def test_comparison_ops(self):
        tokens = Lexer("= != < > <= >=").tokenize()
        types = [t.type for t in tokens]
        assert TokenType.EQ in types
        assert TokenType.NEQ in types
        assert TokenType.LT in types
        assert TokenType.GT in types
        assert TokenType.LTE in types
        assert TokenType.GTE in types

    def test_lexer_error(self):
        with pytest.raises(LexerError):
            Lexer("SELECT ?x WHERE { @invalid }").tokenize()

    def test_keywords(self):
        tokens = Lexer(
            "SELECT DISTINCT COUNT AVG SUM MIN MAX FILTER OPTIONAL UNION ORDER BY GROUP LIMIT OFFSET TEMPORAL CONTEXT PROVENANCE NEIGHBORHOOD"
        ).tokenize()
        types = [t.type for t in tokens]
        assert TokenType.SELECT in types
        assert TokenType.DISTINCT in types


# =====================================================================
# Token
# =====================================================================


class TestToken:
    def test_token_type(self):
        t = Token(TokenType.SELECT, "SELECT")
        assert t.type == TokenType.SELECT

    def test_token_value(self):
        t = Token(TokenType.VARIABLE, "?x")
        assert t.value == "?x"


# =====================================================================
# AST
# =====================================================================


class TestAST:
    def test_select_node(self):
        node = SelectNode(
            NodeType.SELECT,
            columns=(VariableNode(NodeType.VARIABLE, name="?x"),),
        )
        assert len(node.columns) == 1

    def test_literal_node(self):
        n = LiteralNode(NodeType.LITERAL, value=42)
        assert n.value == 42

    def test_variable_node(self):
        n = VariableNode(NodeType.VARIABLE, name="?x")
        assert n.name == "?x"

    def test_comparison_node(self):
        n = ComparisonNode(
            NodeType.COMPARISON,
            op=BinaryOp.GT,
            left=VariableNode(NodeType.VARIABLE, name="?x"),
            right=LiteralNode(NodeType.LITERAL, value=5),
        )
        assert n.op == BinaryOp.GT

    def test_identifier_node(self):
        n = IdentifierNode(NodeType.IDENTIFIER, value="person")
        assert n.value == "person"

    def test_binary_op_node(self):
        n = BinaryOpNode(
            NodeType.BINARY_OP,
            op=BinaryOp.AND,
            left=LiteralNode(NodeType.LITERAL, value=True),
            right=LiteralNode(NodeType.LITERAL, value=False),
        )
        assert n.op == BinaryOp.AND

    def test_function_call_node(self):
        n = FunctionCallNode(
            NodeType.FUNCTION_CALL,
            name="COUNT",
            args=(VariableNode(NodeType.VARIABLE, name="?x"),),
        )
        assert n.name == "COUNT"

    def test_limit_node(self):
        n = ASTLimitNode(NodeType.LIMIT, count=10, offset=5)
        assert n.count == 10
        assert n.offset == 5

    def test_order_node(self):
        n = OrderNode(
            NodeType.ORDER,
            column=VariableNode(NodeType.VARIABLE, name="?x"),
            direction=OrderDirection.DESC,
        )
        assert n.direction == OrderDirection.DESC


# =====================================================================
# Logical Plan
# =====================================================================


class TestLogicalPlan:
    def _scan(self, source="test"):
        return ScanNode(LogicalOperatorType.SCAN, source=source)

    def test_scan_node(self):
        n = self._scan("graph")
        assert n.source == "graph"
        assert n.operator == LogicalOperatorType.SCAN

    def test_selection_node(self):
        n = SelectionNode(LogicalOperatorType.SELECTION, condition="?x > 5")
        assert n.condition == "?x > 5"

    def test_projection_node(self):
        n = ProjectionNode(LogicalOperatorType.PROJECTION, expressions=("?x",), distinct=True)
        assert n.distinct

    def test_join_node(self):
        n = JoinNode(LogicalOperatorType.JOIN, condition="?x = ?y", join_type="inner")
        assert n.condition == "?x = ?y"

    def test_aggregate_node(self):
        n = AggregateNode(
            LogicalOperatorType.AGGREGATE,
            function="COUNT",
            aggregate_column="?x",
            group_by=("?y",),
        )
        assert n.function == "COUNT"

    def test_sort_node(self):
        n = SortNode(LogicalOperatorType.SORT, sort_columns=(("?x", "ASC"),))
        assert len(n.sort_columns) == 1

    def test_limit_node(self):
        n = LimitNode(LogicalOperatorType.LIMIT, limit=10, offset=5)
        assert n.limit == 10

    def test_filter_node(self):
        n = FilterNode(LogicalOperatorType.FILTER, condition="?x > 5")
        assert n.condition == "?x > 5"

    def test_temporal_filter_node(self):
        n = TemporalFilterNode(LogicalOperatorType.TEMPORAL_FILTER, start="2020", end="2024")
        assert n.start == "2020"

    def test_logical_plan_builder(self):
        builder = LogicalPlanBuilder()
        ast = SelectNode(
            NodeType.SELECT, source=IdentifierNode(NodeType.IDENTIFIER, value="graph")
        )
        plan = builder.build(ast)
        assert isinstance(plan, LogicalPlan)
        assert len(plan.nodes) > 0

    def test_logical_plan_to_text(self):
        plan = LogicalPlan(
            root=ScanNode(LogicalOperatorType.SCAN, source="test"),
            estimated_cost=10.0,
            nodes=(),
        )
        text = logical_plan_to_text(plan)
        assert "Scan" in text or "SCAN" in text


# =====================================================================
# Optimizer
# =====================================================================


class TestOptimizer:
    def test_cost_model(self):
        m = CostModel()
        assert m.estimate_scan("test") == 10.0
        assert m.estimate_selection("?x", 100) == 50.0

    def test_constant_folding(self):
        rule = ConstantFolding()
        s = ScanNode(LogicalOperatorType.SCAN, source="g")
        node = SelectionNode(
            LogicalOperatorType.SELECTION,
            condition="?x",
            predicate=True,
            children=(s,),
        )
        result = rule.apply(node)
        assert result.operator == LogicalOperatorType.SCAN

    def test_constant_folding_false(self):
        rule = ConstantFolding()
        node = SelectionNode(
            LogicalOperatorType.SELECTION,
            condition="?x",
            predicate=False,
        )
        result = rule.apply(node)
        assert result.operator == LogicalOperatorType.SCAN
        assert getattr(result, "source", "") == "__empty__"

    def test_dead_operator(self):
        rule = DeadOperatorRemoval()
        s = ScanNode(LogicalOperatorType.SCAN, source="g")
        node = LimitNode(LogicalOperatorType.LIMIT, limit=0, offset=0, children=(s,))
        result = rule.apply(node)
        assert result.operator == LogicalOperatorType.SCAN
        assert getattr(result, "source", "") == "__empty__"

    def test_logical_simplification(self):
        rule = LogicalSimplification()
        s = ScanNode(LogicalOperatorType.SCAN, source="g")
        node = ProjectionNode(LogicalOperatorType.PROJECTION, expressions=(), children=(s,))
        result = rule.apply(node)
        assert result.operator == LogicalOperatorType.SCAN

    def test_optimizer_pipeline(self):
        opt = QueryOptimizer()
        root = ScanNode(LogicalOperatorType.SCAN, source="g")
        plan = LogicalPlan(root=root, estimated_cost=5.0, nodes=(root,))
        result = opt.optimize(plan)
        assert isinstance(result, LogicalPlan)

    def test_optimizer_rules(self):
        opt = QueryOptimizer()
        s = ScanNode(LogicalOperatorType.SCAN, source="g")
        p = ProjectionNode(LogicalOperatorType.PROJECTION, expressions=(), children=(s,))
        sel = SelectionNode(
            LogicalOperatorType.SELECTION,
            condition="?x > 5",
            predicate=True,
            children=(p,),
        )
        plan = LogicalPlan(root=sel, estimated_cost=10.0, nodes=(sel,))
        opt.optimize(plan)
        assert len(opt.applied_rules()) > 0


# =====================================================================
# Physical Plans
# =====================================================================


class TestPhysicalPlans:
    def _scan(self, source="g"):
        return ScanNode(LogicalOperatorType.SCAN, source=source)

    def test_kg_build(self):
        plan = LogicalPlan(root=self._scan("person"), estimated_cost=1.0, nodes=())
        pp = KGPhysicalPlanBuilder().build(plan)
        assert pp.root.operator == PhysicalOperatorType.KG_INDEX_SEEK
        assert pp.engine_type == EngineType.KNOWLEDGE_GRAPH

    def test_kg_selection(self):
        s = self._scan("g")
        sel = SelectionNode(LogicalOperatorType.SELECTION, condition="?x > 5", children=(s,))
        plan = LogicalPlan(root=sel, estimated_cost=2.0, nodes=())
        pp = KGPhysicalPlanBuilder().build(plan)
        assert pp.root.operator == PhysicalOperatorType.KG_FILTER

    def test_sheaf_build(self):
        plan = LogicalPlan(root=self._scan("entity"), estimated_cost=1.0, nodes=())
        pp = SheafPhysicalPlanBuilder().build(plan)
        assert pp.root.operator == PhysicalOperatorType.SHEAF_OPEN_SET_LOOKUP

    def test_physical_plan_to_text(self):
        pp = PhysicalPlan(
            root=PhysicalPlanNode(operator=PhysicalOperatorType.KG_INDEX_SEEK, detail="test"),
            engine_type=EngineType.KNOWLEDGE_GRAPH,
            estimated_cost=5.0,
        )
        text = physical_plan_to_text(pp)
        assert "KG_INDEX_SEEK" in text


# =====================================================================
# Canonical Results
# =====================================================================


class TestCanonical:
    def test_empty(self):
        r = CanonicalResult(columns=(), rows=())
        assert r.row_count == 0

    def test_single_row(self):
        r = CanonicalResult(
            columns=(CanonicalColumn(name="x"),),
            rows=(CanonicalRow(values=(Value(42),)),),
        )
        assert r.row_count == 1

    def test_to_dicts(self):
        r = CanonicalResult(
            columns=(CanonicalColumn(name="name"), CanonicalColumn(name="age")),
            rows=(
                CanonicalRow(values=(Value("Alice"), Value(30))),
                CanonicalRow(values=(Value("Bob"), Value(25))),
            ),
        )
        dicts = r.to_dicts()
        assert dicts[0]["name"] == "Alice"
        assert dicts[1]["age"] == 25

    def test_pretty_string(self):
        r = CanonicalResult(
            columns=(CanonicalColumn(name="x"),),
            rows=(CanonicalRow(values=(Value(42),)),),
        )
        s = r.to_pretty_string()
        assert "42" in s

    def test_addition(self):
        c = (CanonicalColumn(name="x"),)
        r1 = CanonicalResult(columns=c, rows=(CanonicalRow(values=(Value(1),)),))
        r2 = CanonicalResult(columns=c, rows=(CanonicalRow(values=(Value(2),)),))
        r3 = r1 + r2
        assert r3.row_count == 2


# =====================================================================
# Cache
# =====================================================================


class TestCache:
    def test_lru_basic(self):
        c = LRUCache(max_size=3)
        c.put(1, "a")
        c.put(2, "b")
        assert c.get(1) == "a"
        assert c.get(3) is None

    def test_lru_eviction(self):
        c = LRUCache(max_size=2)
        c.put(1, "a")
        c.put(2, "b")
        c.put(3, "c")
        assert c.get(1) is None
        assert c.get(3) == "c"

    def test_hit_rate(self):
        c = LRUCache(max_size=10)
        c.put(1, "a")
        c.get(1)
        c.get(2)
        assert c.hit_rate() == 0.5

    def test_query_cache(self):
        qc = QueryCache(max_entries=10)
        qc.parsed.put(1, "ast")
        qc.logical.put(2, "plan")
        assert qc.parsed.get(1) == "ast"

    def test_clear(self):
        qc = QueryCache()
        qc.parsed.put(1, "x")
        qc.clear_all()
        assert qc.parsed.get(1) is None


# =====================================================================
# Statistics
# =====================================================================


class TestStatistics:
    def test_register(self):
        s = StatisticsStore()
        s.register("people", TableStatistics(row_count=100))
        assert s.get("people").row_count == 100

    def test_selectivity(self):
        s = StatisticsStore()
        s.register("people", TableStatistics(row_count=100))
        s.update_distinct("people", "age", 50)
        sel = s.estimate_selectivity("people", "age")
        assert abs(sel - 0.02) < 0.001

    def test_all_stats(self):
        s = StatisticsStore()
        s.register("a", TableStatistics(row_count=10))
        s.register("b", TableStatistics(row_count=20))
        assert len(s.all_stats()) == 2


# =====================================================================
# Benchmark
# =====================================================================


class TestBenchmark:
    def test_record(self):
        b = BenchmarkCollector()
        b.record(
            BenchmarkEntry(query_text="SELECT ?x", engine="KG", execution_time_ms=5.0, row_count=1)
        )
        assert b.summary()["entries"] == 1

    def test_export(self):
        b = BenchmarkCollector()
        b.record(
            BenchmarkEntry(query_text="SELECT ?x", engine="KG", execution_time_ms=5.0, row_count=1)
        )
        exported = b.export_results()
        assert len(exported) == 1

    def test_clear(self):
        b = BenchmarkCollector()
        b.record(
            BenchmarkEntry(query_text="SELECT ?x", engine="KG", execution_time_ms=5.0, row_count=1)
        )
        b.clear()
        assert b.summary()["entries"] == 0


# =====================================================================
# Execution Engine
# =====================================================================


class TestExecution:
    def test_execute_simple(self):
        engine = QueryExecutionEngine()
        result = engine.execute_query("SELECT ?x FROM test WHERE ?x > 5")
        assert result.canonical is not None
        assert result.execution_plan is not None

    def test_explain(self):
        engine = QueryExecutionEngine()
        text = engine.explain("SELECT ?x FROM test WHERE ?x > 5")
        assert "Logical Plan" in text

    def test_explain_analyze(self):
        engine = QueryExecutionEngine()
        text = engine.explain_analyze("SELECT ?x FROM test WHERE ?x > 5")
        assert "Physical Plan" in text or "Logical Plan" in text

    def test_benchmark(self):
        engine = QueryExecutionEngine()
        text = engine.benchmark("SELECT ?x FROM test WHERE ?x > 5")
        assert "Benchmark" in text or "Rows" in text
