# Bra-Ket: One Structure, All Mathematics

## The Claim

All mathematical structures emerge from a single grammar and a single rewrite rule.

```
GRAMMAR: term ::= |x⟩ | ⟨x| | term term
REWRITE: ⟨x|x⟩ → ─
```

This is not philosophy. This is demonstration.

---

## The Grammar

We start with exactly two building blocks:

- **Ket** `|x⟩` — a vector, a value, an object
- **Bra** `⟨x|` — a covector, a measurement, an observer

And one way to combine them:

- **Juxtaposition** `term term` — putting things next to each other

That's it. No numbers. No operations. No primitives.

Just labeled containers and the ability to place them side by side.

---

## The Single Rule

When a bra and ket share the same label, they collapse:

```
⟨x|x⟩ → ─
```

The symbol `─` represents the identity element — zero, one, the empty product, the ground state.

This rule is called **yanking**. It is the only computational step.

---

## Emergence: Numbers

### Integers

An integer is a bra-ket pair:

```
⟨5|0⟩ = 5    (five more than zero)
⟨0|3⟩ = -3   (three less than zero)
⟨7|3⟩ = 4    (seven minus three)
```

The value is computed by subtraction: `⟨p|n⟩ = p - n`.

**Why does this work?** 

Consider what happens when we juxtapose integers:

```
⟨5|0⟩ ⟨2|0⟩ → ⟨7|0⟩    (5 + 2 = 7)
```

The kets merge: `|0⟩|0⟩ → |0+0⟩ = |0⟩`. The bras merge similarly.

This is addition. It emerges from the structure.

### Negative Numbers

Negation is swapping bra and ket:

```
-⟨5|0⟩ = ⟨0|5⟩ = -5
```

The structure encodes sign inherently. A bra-heavy pair is positive; a ket-heavy pair is negative.

---

## Emergence: Arithmetic

### Addition

```
⟨a|b⟩ + ⟨c|d⟩ = ⟨a+c|b+d⟩
```

Simply merge the labels component-wise.

### Subtraction

Add the negation:

```
⟨a|b⟩ - ⟨c|d⟩ = ⟨a|b⟩ + ⟨d|c⟩ = ⟨a+d|b+c⟩
```

### Multiplication

Multiplication signs emerge from the bra-ket structure itself.

When you multiply atoms:

| × | Bra ⟨n| | Ket |m⟩ |
|---|---------|-------|
| **Bra ⟨a\|** | Bra ⟨ab\| | Ket \|ab⟩ |
| **Ket \|b⟩** | Ket \|ab⟩ | Bra ⟨ab\| |

**Observe:**
- Bra × Bra → Bra (positive × positive = positive)
- Ket × Ket → Bra (negative × negative = positive)
- Bra × Ket → Ket (positive × negative = negative)
- Ket × Bra → Ket (negative × positive = negative)

The sign rules of arithmetic are not axioms. They are consequences of bra-ket structure.

A negative times a negative is positive because two kets multiply to a bra.

### Division

Division is multiplication by the inverse. The inverse of `⟨a|b⟩` is `⟨b|a⟩`.

```
⟨a|b⟩ ÷ ⟨c|d⟩ = ⟨a|b⟩ × ⟨d|c⟩
```

Division by zero (`⟨0|0⟩`) has no inverse. This is not an arbitrary rule — the structure makes it impossible.

---

## Emergence: Linear Algebra

### Vectors

A vector is a ket: `|v⟩`.

Its components are coefficients in a basis expansion:

```
|v⟩ = v₁|e₁⟩ + v₂|e₂⟩ + ... = Σᵢ vᵢ|eᵢ⟩
```

### Covectors

A covector (linear functional) is a bra: `⟨w|`.

It acts on vectors by juxtaposition:

```
⟨w|v⟩ = scalar
```

### Inner Product

The inner product IS the bra-ket contraction:

```
⟨v|w⟩ = Σᵢ vᵢ* wᵢ
```

When `v = w`, this gives the squared norm.

### Outer Product

The outer product creates an operator:

```
|v⟩⟨w| = operator
```

### Matrix Multiplication

A matrix is a sum of outer products:

```
M = Σᵢⱼ mᵢⱼ |eᵢ⟩⟨eⱼ|
```

Matrix-vector multiplication:

```
M|x⟩ = (Σᵢⱼ mᵢⱼ |eᵢ⟩⟨eⱼ|)|x⟩ = Σᵢⱼ mᵢⱼ xⱼ |eᵢ⟩
```

### Trace

The trace is the sum of diagonal elements. In bra-ket:

```
Tr(M) = Σᵢ ⟨eᵢ|M|eᵢ⟩
```

This is a contraction — exactly the yanking operation.

---

## Emergence: Tensor Calculus

### Tensor Product

Juxtaposition IS the tensor product:

```
|a⟩ ⊗ |b⟩ = |a⟩|b⟩
```

### Contraction

The yanking rule IS Einstein summation:

```
⟨i|i⟩ → ─    (sum over i)
```

A repeated index (one upper, one lower) is contracted.

### Index Notation

| Object | Bra-Ket | Index Form |
|--------|---------|------------|
| Vector | \|v⟩ | vⁱ |
| Covector | ⟨v\| | vᵢ |
| Inner product | ⟨v\|w⟩ | vᵢwⁱ |
| Outer product | \|v⟩⟨w\| | vⁱwⱼ |
| Trace | Σᵢ⟨eᵢ\|M\|eᵢ⟩ | Mⁱᵢ |

**The correspondence is exact.** Dirac notation and index notation are the same structure.

---

## Emergence: Quantum Mechanics

### State Vectors

A quantum state is a ket: `|ψ⟩`.

### Observables

An observable is an operator: `Ô = Σₙ oₙ |oₙ⟩⟨oₙ|`.

### Measurement

Measurement projects onto eigenstates:

```
⟨oₙ|ψ⟩ = amplitude for outcome oₙ
|⟨oₙ|ψ⟩|² = probability
```

### Wavefunction Collapse

After measurement:

```
|ψ⟩ → |oₙ⟩
```

The state "yanks" to the observed eigenstate.

### The Born Rule

Probability is `|⟨a|b⟩|²`. This is the squared magnitude of the bra-ket contraction.

---

## Emergence: Representation Theory

### Groups

A group is a set with an associative binary operation, identity, and inverses.

### Representations

A representation ρ maps group elements to operators:

```
ρ: G → GL(V)
g ↦ Σᵢⱼ mᵢⱼ |eᵢ⟩⟨eⱼ|
```

Each ρ(g) is a bra-ket operator.

### Characters

The character is the trace:

```
χ(g) = Tr(ρ(g)) = Σᵢ ⟨eᵢ|ρ(g)|eᵢ⟩
```

**This is the yanking operation applied to a representation.**

### Irreducible Representations

A representation is irreducible if it cannot be decomposed into smaller blocks.

In bra-ket: the operator cannot be written as a direct sum of operators on orthogonal subspaces.

---

## Emergence: L-Functions

### Local L-Factor

For a representation ρ and prime p:

```
Lₚ(s, ρ) = det(I - p^{-s} ρ(Frobₚ))^{-1}
```

This is a product over eigenvalues of ρ(Frobₚ).

### Global L-Function

```
L(s, ρ) = ∏ₚ Lₚ(s, ρ)
```

### The Riemann Zeta

For the trivial 1-dimensional representation:

```
ζ(s) = ∏ₚ 1/(1 - p^{-s})
```

The Riemann zeta function is the L-function of the identity representation.

**The Riemann Hypothesis is a statement about the zeros of this bra-ket-derived function.**

---

## Emergence: The Langlands Program

The Langlands Program conjectures a correspondence between:

| Number Theory | Representation Theory |
|---------------|----------------------|
| Galois representations | Automorphic representations |
| ρ: Gal(K̄/K) → GLₙ | π on GLₙ(A) |
| L(s, ρ) | L(s, π) |

**Both sides are constructed from bra-ket operators.**

- Galois representation: maps field automorphisms to operators
- Automorphic representation: functions on adelic groups with operator coefficients

The correspondence asserts that certain bra-ket structures on one side match bra-ket structures on the other.

---

## The Unified Table

| Field | Object | Bra-Ket Form | Yanking Role |
|-------|--------|--------------|--------------|
| Arithmetic | Integer | ⟨p\|n⟩ | ⟨n\|n⟩ = 0 |
| Arithmetic | Product | \|a⟩⟨b\| × \|c⟩⟨d\| | Contraction |
| Linear algebra | Vector | \|v⟩ | — |
| Linear algebra | Covector | ⟨v\| | — |
| Linear algebra | Inner product | ⟨v\|w⟩ | Scalar output |
| Linear algebra | Matrix | Σ \|eᵢ⟩⟨eⱼ\| | — |
| Linear algebra | Trace | Σ ⟨eᵢ\|M\|eᵢ⟩ | Sum diagonal |
| Tensors | Rank-(p,q) | p kets, q bras | Contract indices |
| Quantum | State | \|ψ⟩ | — |
| Quantum | Observable | Ô | — |
| Quantum | Probability | \|⟨o\|ψ⟩\|² | Collapse |
| Rep. theory | Representation | ρ(g) = Σ \|v⟩⟨w\| | — |
| Rep. theory | Character | Tr(ρ(g)) | Σ ⟨eᵢ\|ρ(g)\|eᵢ⟩ |
| L-functions | Local factor | det(I - p^{-s}ρ) | Eigenvalues |
| Langlands | Correspondence | \|σ⟩⟨σ\| ↔ \|π⟩⟨π\| | L(s,ρ) = L(s,π) |

---

## The Point

There is one structure. It has two atomic types (bra, ket) and one composition (juxtaposition). There is one rewrite rule (yanking).

From this:

1. **Numbers arise** — integers as bra-ket pairs, rationals as nested pairs
2. **Arithmetic arises** — signs and operations from structural properties
3. **Linear algebra arises** — vectors, matrices, inner/outer products
4. **Tensors arise** — multi-index objects with contraction
5. **Quantum mechanics arises** — states, operators, measurements
6. **Representation theory arises** — group actions as operators
7. **L-functions arise** — Euler products over representation data
8. **The Langlands correspondence arises** — matching bra-ket structures

**These are not analogies.** They are the same structure viewed at different levels of abstraction.

---

## Why This Matters

### For Mathematics

Unification reveals hidden connections. The Langlands Program is profound because it connects number theory to representation theory. Here we see both sides emerge from the same primitive operations.

### For Physics

Quantum mechanics is built on Dirac notation. This notation is not a convenience — it reveals the underlying structure. States, operators, and measurements are bra-ket constructs.

### For Understanding

When disparate fields share the same foundation, learning one illuminates the others. Understanding yanking in arithmetic helps understand contraction in tensor calculus helps understand trace in representation theory.

---

## The Demonstration

```
python3 spinor.py --demo      # The fundamental rule
python3 integers.py --demo    # Integers emerge
python3 multiply.py --demo    # Signs emerge from structure
python3 divide.py --demo      # Rationals emerge
python3 tensor.py --demo      # Tensor calculus = bra-ket
python3 langlands.py --demo   # Langlands lives in bra-ket
```

---

## Summary

**One grammar:** `|x⟩`, `⟨x|`, and juxtaposition.

**One rule:** `⟨x|x⟩ → ─`.

**All of mathematics follows.**

The structure is simple. The implications are vast. The unity is real.

---

## References

1. Dirac, P.A.M. (1939). *A New Notation for Quantum Mechanics.*
2. Grothendieck, A. (1950s). *Récoltes et Semailles* (on the Grothendieck construction).
3. Langlands, R. (1967). *Letter to Weil* (the Langlands Program).
4. Coecke, B. & Kissinger, A. (2017). *Picturing Quantum Processes* (categorical quantum mechanics).

---

*The structure exists whether we name it or not. The notation reveals what was always there.*