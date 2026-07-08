"""LUBM (Lehigh University Benchmark) data loader.

Generates LUBM-compatible data as SemanticFact instances for
standardized benchmarking.  LUBM is the de-facto standard for
RDF store evaluation; having a LUBM loader enables direct
comparison against published results.

The loader generates a configurable number of universities with
departments, professors, students, courses, and publications,
mapped to the LUBM ontology.

Reference: http://swat.cse.lehigh.edu/projects/lubm/
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from common.schema import SemanticFact
from common.types import Context, Identifier, Provenance, Value


@dataclass
class LUBMConfig:
    """Configuration for LUBM dataset generation.

    Attributes:
        num_universities: Number of universities to generate.
        seed: Random seed for reproducibility.
        context_depth: Depth of context hierarchy.
    """

    num_universities: int = 1
    seed: int = 42
    context_depth: int = 3


class LUBMGenerator:
    """Generates LUBM-compatible benchmark data.

    Produces SemanticFact instances representing the LUBM university
    ontology: departments, professors, students, courses, publications,
    and their relationships.

    The generator creates a tree-structured context hierarchy matching
    the university structure:
        world → world.<univ> → world.<univ>.<dept>
    """

    # LUBM ontology predicates
    PREDICATES = {
        "worksFor": "http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#worksFor",
        "headOf": "http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#headOf",
        "teacherOf": "http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#teacherOf",
        "takesCourse": "http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#takesCourse",
        "advisor": "http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#advisor",
        "memberOf": "http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#memberOf",
        "publicationAuthor": "http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#publicationAuthor",
        "subordinateOf": "http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#subordinateOf",
        "doctoralDegreeFrom": "http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#doctoralDegreeFrom",
        "undergraduateDegreeFrom": "http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#undergraduateDegreeFrom",
    }

    # LUBM standard query templates (14 queries)
    QUERIES: dict[str, str] = {
        "Q1": "SELECT ?x WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#GraduateStudent> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#takesCourse> <http://www.Department0.University0.edu/GraduateCourse0> }",
        "Q2": "SELECT ?x ?y ?z WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#GraduateStudent> . ?y <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#University> . ?z <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Department> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#memberOf> ?z . ?z <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#subOrganizationOf> ?y . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#undergraduateDegreeFrom> ?y }",
        "Q3": "SELECT ?x WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Publication> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#publicationAuthor> <http://www.Department0.University0.edu/AssistantProfessor0> }",
        "Q4": "SELECT ?x ?y1 ?y2 ?y3 WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Professor> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#worksFor> <http://www.Department0.University0.edu> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#name> ?y1 . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#emailAddress> ?y2 . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#telephone> ?y3 }",
        "Q5": "SELECT ?x WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Person> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#memberOf> <http://www.Department0.University0.edu> }",
        "Q6": "SELECT ?x WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Student> }",
        "Q7": "SELECT ?x ?y WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Student> . ?y <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Course> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#takesCourse> ?y }",
        "Q8": "SELECT ?x ?y ?z WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Student> . ?y <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Department> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#memberOf> ?y . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#emailAddress> ?z }",
        "Q9": "SELECT ?x ?y ?z WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Student> . ?y <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Faculty> . ?z <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Course> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#advisor> ?y . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#takesCourse> ?z }",
        "Q10": "SELECT ?x WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Student> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#takesCourse> <http://www.Department0.University0.edu/GraduateCourse0> }",
        "Q11": "SELECT ?x WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#ResearchGroup> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#subOrganizationOf> <http://www.University0.edu> }",
        "Q12": "SELECT ?x WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Chair> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#worksFor> <http://www.Department0.University0.edu> }",
        "Q13": "SELECT ?x WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#Person> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#doctoralDegreeFrom> <http://www.University0.edu> }",
        "Q14": "SELECT ?x WHERE { ?x <rdf:type> <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#UndergraduateStudent> . ?x <http://www.lehigh.edu/~zhp2/2004/0401/univ-bench.owl#memberOf> <http://www.Department0.University0.edu> }",
    }

    def __init__(self, config: LUBMConfig) -> None:
        self._config = config
        self._rng = random.Random(config.seed)
        self._facts: list[SemanticFact] = []
        self._fact_id_counter: int = 0

    def _next_id(self) -> Identifier:
        self._fact_id_counter += 1
        return Identifier(f"lubm_fact_{self._fact_id_counter}")

    def _entity_id(self, name: str) -> Identifier:
        return Identifier(name)

    def _context(self, *segments: str) -> Context:
        return Context(".".join(segments))

    def _add_fact(
        self,
        subject: Identifier,
        relation: str,
        objects: tuple[Value, ...],
        context: Context,
        attributes: dict[str, Value] | None = None,
    ) -> None:
        fact = SemanticFact(
            id=self._next_id(),
            subject=subject,
            relation=Identifier(relation),
            objects=objects,
            attributes=attributes or {},
            context=context,
            provenance=Provenance(source="lubm_generator", method="synthetic"),
        )
        self._facts.append(fact)

    def generate(self) -> list[SemanticFact]:
        """Generate LUBM-compatible facts."""
        self._facts = []
        self._fact_id_counter = 0

        for univ_idx in range(self._config.num_universities):
            univ_name = f"University{univ_idx}"
            univ_entity = self._entity_id(f"http://www.{univ_name}.edu")
            univ_ctx = self._context("world", univ_name)

            # University entity
            self._add_fact(
                univ_entity,
                "rdf:type",
                (Value.literal("University"),),
                univ_ctx,
            )

            # Generate departments
            num_depts = self._rng.randint(2, 5)
            for dept_idx in range(num_depts):
                dept_name = f"Department{dept_idx}.{univ_name}"
                dept_entity = self._entity_id(f"http://www.{dept_name}")
                dept_ctx = self._context("world", univ_name, f"dept{dept_idx}")

                self._add_fact(
                    dept_entity,
                    "rdf:type",
                    (Value.literal("Department"),),
                    dept_ctx,
                )
                self._add_fact(
                    dept_entity,
                    self.PREDICATES["subordinateOf"],
                    (Value.reference(univ_entity),),
                    dept_ctx,
                )

                # Professors
                num_profs = self._rng.randint(3, 8)
                for prof_idx in range(num_profs):
                    prof_name = f"{'Full' if prof_idx < 2 else 'Associate' if prof_idx < 4 else 'Assistant'}Professor{prof_idx}.{dept_name}"
                    prof_entity = self._entity_id(f"http://www.{prof_name}")

                    self._add_fact(
                        prof_entity,
                        "rdf:type",
                        (Value.literal("Professor"),),
                        dept_ctx,
                    )
                    self._add_fact(
                        prof_entity,
                        self.PREDICATES["worksFor"],
                        (Value.reference(dept_entity),),
                        dept_ctx,
                    )

                    # Head of department
                    if prof_idx == 0:
                        self._add_fact(
                            prof_entity,
                            self.PREDICATES["headOf"],
                            (Value.reference(dept_entity),),
                            dept_ctx,
                        )

                    # Courses taught
                    num_courses = self._rng.randint(1, 3)
                    for course_idx in range(num_courses):
                        course_name = f"{'Graduate' if self._rng.random() < 0.3 else 'Undergraduate'}Course{course_idx}.{dept_name}"
                        course_entity = self._entity_id(f"http://www.{course_name}")

                        self._add_fact(
                            course_entity,
                            "rdf:type",
                            (Value.literal("Course"),),
                            dept_ctx,
                        )
                        self._add_fact(
                            prof_entity,
                            self.PREDICATES["teacherOf"],
                            (Value.reference(course_entity),),
                            dept_ctx,
                        )

                    # Publications
                    num_pubs = self._rng.randint(1, 5)
                    for pub_idx in range(num_pubs):
                        pub_name = f"Publication{pub_idx}.{prof_name}"
                        pub_entity = self._entity_id(f"http://www.{pub_name}")

                        self._add_fact(
                            pub_entity,
                            "rdf:type",
                            (Value.literal("Publication"),),
                            dept_ctx,
                        )
                        self._add_fact(
                            pub_entity,
                            self.PREDICATES["publicationAuthor"],
                            (Value.reference(prof_entity),),
                            dept_ctx,
                        )

                # Graduate students
                num_grads = self._rng.randint(2, 6)
                for grad_idx in range(num_grads):
                    grad_name = f"GraduateStudent{grad_idx}.{dept_name}"
                    grad_entity = self._entity_id(f"http://www.{grad_name}")

                    self._add_fact(
                        grad_entity,
                        "rdf:type",
                        (Value.literal("GraduateStudent"),),
                        dept_ctx,
                    )
                    self._add_fact(
                        grad_entity,
                        self.PREDICATES["memberOf"],
                        (Value.reference(dept_entity),),
                        dept_ctx,
                    )

                    # Advisor
                    advisor = self._entity_id(
                        f"http://www.FullProfessor0.{dept_name}"
                    )
                    self._add_fact(
                        grad_entity,
                        self.PREDICATES["advisor"],
                        (Value.reference(advisor),),
                        dept_ctx,
                    )

                    # Takes courses
                    for course_idx in range(self._rng.randint(1, 3)):
                        course_name = f"GraduateCourse{course_idx}.{dept_name}"
                        course_entity = self._entity_id(f"http://www.{course_name}")
                        self._add_fact(
                            grad_entity,
                            self.PREDICATES["takesCourse"],
                            (Value.reference(course_entity),),
                            dept_ctx,
                        )

                # Undergraduate students
                num_undergrads = self._rng.randint(3, 10)
                for ug_idx in range(num_undergrads):
                    ug_name = f"UndergraduateStudent{ug_idx}.{dept_name}"
                    ug_entity = self._entity_id(f"http://www.{ug_name}")

                    self._add_fact(
                        ug_entity,
                        "rdf:type",
                        (Value.literal("UndergraduateStudent"),),
                        dept_ctx,
                    )
                    self._add_fact(
                        ug_entity,
                        self.PREDICATES["memberOf"],
                        (Value.reference(dept_entity),),
                        dept_ctx,
                    )

        return self._facts

    @property
    def num_facts(self) -> int:
        return len(self._facts)

    @property
    def queries(self) -> dict[str, str]:
        return dict(self.QUERIES)
