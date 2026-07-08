# Formal Notation

## Sets and Typed Sets

| Symbol | Meaning | Example |
|--------|---------|---------|
| $\mathbb{N}$ | Natural numbers $\{0,1,2,\ldots\}$ | $0, 1, 2$ |
| $\mathbb{R}$ | Real numbers | $\pi, e$ |
| $\mathcal{P}(X)$ | Power set of $X$ | $\mathcal{P}(\{a,b\}) = \{\emptyset,\{a\},\{b\},\{a,b\}\}$ |
| $|X|$ | Cardinality of $X$ | $|\{a,b\}| = 2$ |
| $X \times Y$ | Cartesian product | $\{(x,y) \mid x \in X, y \in Y\}$ |
| $X \sqcup Y$ | Disjoint union | $\{(x,0) \mid x \in X\} \cup \{(y,1) \mid y \in Y\}$ |
| $X^n$ | $n$-fold product | $X \times X \times \cdots \times X$ ($n$ times) |
| $X^*$ | Finite sequences over $X$ | $\bigsqcup_{n \geq 0} X^n$ |

## Relations and Functions

| Symbol | Meaning | Example |
|--------|---------|---------|
| $f: A \to B$ | Total function from $A$ to $B$ | $f(x) = x^2$ |
| $f: A \rightharpoonup B$ | Partial function | $f(x)$ undefined for some $x$ |
| $g \circ f$ | Composition $(g \circ f)(x) = g(f(x))$ | |
| $\operatorname{dom}(f)$ | Domain of $f$ | |
| $\operatorname{codom}(f)$ | Codomain of $f$ | |
| $\operatorname{im}(f)$ | Image of $f$ | $\{f(x) \mid x \in \operatorname{dom}(f)\}$ |
| $f|_A$ | Restriction of $f$ to subset $A$ | $f|_A(x) = f(x)$ for $x \in A \cap \operatorname{dom}(f)$ |
| $R \subseteq A \times B$ | Binary relation | $aRb$ |
| $\operatorname{id}_X$ | Identity function on $X$ | $\operatorname{id}_X(x) = x$ |
| $\pi_i$ | $i$-th projection | $\pi_i(x_1,\ldots,x_n) = x_i$ |

## Category Theory

| Symbol | Meaning | Example |
|--------|---------|---------|
| $\mathcal{C}$ | A category | $\mathbf{Set}, \mathbf{Pos}$ |
| $\operatorname{Ob}(\mathcal{C})$ | Objects of $\mathcal{C}$ | |
| $\operatorname{Hom}_{\mathcal{C}}(A,B)$ | Morphisms $A \to B$ in $\mathcal{C}$ | |
| $F: \mathcal{C} \to \mathcal{D}$ | Functor from $\mathcal{C}$ to $\mathcal{D}$ | |
| $\mathcal{C}^{\text{op}}$ | Opposite category (morphisms reversed) | |
| $F \dashv G$ | Adjunction: $F$ left adjoint to $G$ | |
| $\mathbf{Set}$ | Category of sets and functions | |
| $\mathbf{Pos}$ | Category of posets and monotone maps | |

## Posets and Topology

| Symbol | Meaning | Example |
|--------|---------|---------|
| $(P, \leq)$ | Poset with order relation $\leq$ | |
| $\downarrow x$ | Down-set of $x$: $\{y \in P \mid y \leq x\}$ | |
| $\uparrow x$ | Up-set of $x$: $\{y \in P \mid x \leq y\}$ | |
| $x \wedge y$ | Meet (greatest lower bound) | |
| $x \vee y$ | Join (least upper bound) | |
| $x < y$ | Strict order: $x \leq y$ and $x \neq y$ | |
| $\perp$ | Bottom element (if exists) | |
| $\top$ | Top element (if exists) | |
| $(X, \mathcal{T})$ | Topological space: $X$ points, $\mathcal{T}$ open sets | |
| $\mathcal{T}$ | Topology: collection of open subsets of $X$ | |
| $U \in \mathcal{T}$ | Open set $U$ | |
| $\overline{U}$ | Closure of $U$ | |
| $\partial U$ | Boundary of $U$ | |
| $\mathcal{N}(x)$ | Neighbourhood filter of $x$ | $\{U \in \mathcal{T} \mid x \in U\}$ |

## Alexandrov Topology

| Symbol | Meaning | Example |
|--------|---------|---------|
| $\mathcal{T}_A(P)$ | Alexandrov topology on poset $P$ | All down-sets are open |
| $\operatorname{int}(S)$ | Interior of $S$ (largest open subset) | |
| $\operatorname{cl}(S)$ | Closure of $S$ (smallest closed superset) | |
| $\mathcal{B}(x)$ | Minimal open set containing $x$ | $\mathcal{B}(x) = \downarrow x$ in Alexandrov topology |

## Presheaves and Sheaves

| Symbol | Meaning | Example |
|--------|---------|---------|
| $F$ | A presheaf or sheaf | |
| $F(U)$ | Sections over open set $U$ | |
| $\rho_{V,U}: F(V) \to F(U)$ | Restriction map for $U \subseteq V$ | |
| $s|_U$ | Shorthand for $\rho_{V,U}(s)$ when $s \in F(V)$ | |
| $\Gamma(X, F)$ | Global sections $F(X)$ | |
| $F_x$ | Stalk at point $x$ | $\varinjlim_{U \ni x} F(U)$ |
| $[s]_x$ | Germ of section $s$ at $x$ | Equivalence class in $F_x$ |
| $\check{H}^i(X, F)$ | Čech cohomology groups | |

## Semantic Fact Model

| Symbol | Meaning | Example |
|--------|---------|---------|
| $\mathcal{I}$ | Set of identifiers (UUIDs) | |
| $\mathcal{E}$ | Set of entities | $\mathcal{E} \subset \mathcal{I}$ |
| $\mathcal{R}$ | Set of relation types | $\mathcal{R} \subset \mathcal{I}$ |
| $\mathcal{V}$ | Set of values | $\mathcal{V} = \mathcal{I} \sqcup \mathbb{L}$ |
| $\mathbb{L}$ | Set of literals (strings, numbers, booleans) | |
| $\mathcal{C}$ | Set of contexts | Poset $(\mathcal{C}, \leq)$ |
| $\mathcal{F}$ | Set of all possible facts | |
| $\mathcal{K}$ | Set of knowledge states | $\mathcal{K} = \bigcup_{c \in \mathcal{C}} \mathcal{P}(\mathcal{F}_c)$ |

## Specific Symbols Used Throughout

| Symbol | Meaning |
|--------|---------|
| $\sigma, \tau$ | Sections (facts) |
| $s, t$ | Sections (general) |
| $c, d, e$ | Contexts (elements of $\mathcal{C}$) |
| $x, y, z$ | Points (elements of topological space $X$) |
| $U, V, W$ | Open sets |
| $\Sigma$ | Knowledge state (set of sections) |
| $\varepsilon$ | Entity |
| $\rho$ | Relation |
| $\omega$ | Value (object slot) |
| $\mathfrak{F}$ | Canonical model |
| $Q$ | Query |
| $\llbracket Q \rrbracket$ | Denotation (result) of query $Q$ |
