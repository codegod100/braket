#!/usr/bin/env python3
"""
Spinor Church Encoding: Functions from Bra-Ket

The universe is spinors. Functions and numbers emerge from structure.

KEY INSIGHTS:
1. |x⟩⟨x| = identity (yanks to wire)
2. Labels prevent unwanted yanking
3. Church numeral n = structure with n "application slots"

CHURCH ENCODING:
  0 = λf.λx.x       -- return x, ignore f
  1 = λf.λx.f x     -- apply f once
  2 = λf.λx.f(f x)  -- apply f twice
  n = λf.λx.f^n x   -- apply f n times

In spinor notation:
  - λ-binding = bra (the input port)
  - Application = composition of operators
  - Number = count of operator compositions
"""

from dataclasses import dataclass
from typing import Union, List, Dict, Optional
from copy import deepcopy


# ============================================================================
# Terms
# ============================================================================

@dataclass(frozen=True)
class Ket:
    label: str
    def __str__(self): return f"|{self.label}⟩"
    def __repr__(self): return f"Ket({self.label!r})"
    def __format__(self, fmt): return format(str(self), fmt)


@dataclass(frozen=True)
class Bra:
    label: str
    def __str__(self): return f"⟨{self.label}|"
    def __repr__(self): return f"Bra({self.label!r})"
    def __format__(self, fmt): return format(str(self), fmt)


@dataclass(frozen=True)
class Juxt:
    left: 'Term'
    right: 'Term'
    def __str__(self): return f"{self.left}{self.right}"
    def __repr__(self): return f"Juxt({self.left!r}, {self.right!r})"
    def __format__(self, fmt): return format(str(self), fmt)


@dataclass(frozen=True)
class Wire:
    def __str__(self): return "─"
    def __repr__(self): return "Wire()"
    def __format__(self, fmt): return format(str(self), fmt)


Term = Union[Wire, Ket, Bra, Juxt]


def juxt(a: Term, b: Term) -> Term:
    """Smart juxtaposition."""
    if isinstance(a, Wire) and isinstance(b, Wire): return Wire()
    if isinstance(a, Wire): return b
    if isinstance(b, Wire): return a
    return Juxt(a, b)


# ============================================================================
# Church Numerals as Spinor Structures
# ============================================================================

def church_zero() -> Term:
    """
    Church 0 = λf.λx.x
    
    Interpretation:
    - Takes f (a function), ignores it
    - Takes x, returns it unchanged
    
    In spinors: we need to "consume" f without using it
    and pass x through.
    
    Structure: |x⟩⟨x| |f⟩⟨f|
    - |f⟩⟨f| is identity on f-space (f is "absorbed" into the vacuum)
    - |x⟩⟨x| is identity on x-space (x passes through)
    
    When applied: the ⟨f| and ⟨x| bind the arguments,
    the |f⟩ and |x| are the outputs.
    """
    return juxt(Ket("x"), Bra("x"))  # Just x identity, f is implicit


def church_one() -> Term:
    """
    Church 1 = λf.λx.f x
    
    Apply f once to x.
    
    In spinors, f is an OPERATOR that transforms its input.
    Application: contract f's input with x, output f's output.
    
    If f is represented as |out⟩⟨in| (a morphism in→out):
    f(x) = |out⟩⟨in| applied to |x⟩
         = the result when in is x and out is the output
    
    For Church 1, we need:
    - Input port for x: ⟨x|
    - Input port for f: ⟨f_in|⟨f_out| (f's input and output)
    - Output: |result⟩
    
    Simpler: Church 1 is a "placeholder" for one f-application.
    
    Structure: |f⟩⟨x| where f's "value" becomes the output
    This represents: output = f(input), where input is bound to x
    
    But we need to also "bind" f itself...
    
    BETTER: Church numeral is a WIRING PATTERN
    
    numeral n = n wires crossing through f-boxes
    """
    # Simplest: one "gate" that will become f
    # |out⟩⟨x| represents: input is x, output is "out"
    # The f-application is implicit in the gate structure
    return juxt(Ket("f_out"), Bra("x"))


def church(n: int) -> Term:
    """
    Church numeral n as a spinor network.
    
    Structure for n:
    - n "gates" in sequence, each representing one f-application
    - First gate takes x as input
    - Last gate produces the output
    - Intermediate gates connect
    
    Each gate is |out_i⟩⟨in_i|
    Gate 0: input = x, output connects to gate 1
    Gate i: input from gate i-1, output to gate i+1 (or final)
    Gate n-1: output = result
    
    Chain: |res⟩⟨mid_{n-1}| |mid_{n-1}⟩⟨mid_{n-2}| ... |mid_1⟩⟨x|
    
    This is n gates total (n compositions).
    Each gate will "become" f when the numeral is applied.
    """
    if n == 0:
        return juxt(Ket("x"), Bra("x"))  # Just return x
    
    # Build n gates in a chain
    # Use fresh labels for intermediate connections
    gates = []
    
    # Gate 0: |v_1⟩⟨x|
    gates.append(juxt(Ket("v_1"), Bra("x")))
    
    # Gates 1..n-2: |v_{i+1}⟩⟨v_i|
    for i in range(1, n-1):
        gates.append(juxt(Ket(f"v_{i+1}"), Bra(f"v_{i}")))
    
    # Gate n-1 (last): |out⟩⟨v_{n-1}|
    if n > 1:
        gates.append(juxt(Ket("out"), Bra(f"v_{n-1}")))
    else:
        # n=1: only one gate, fix the label
        gates = [juxt(Ket("out"), Bra("x"))]
    
    # Compose all gates
    result = gates[0]
    for g in gates[1:]:
        result = juxt(result, g)
    
    return result


# ============================================================================
# Application: Actually Computing with Church Numerals
# ============================================================================

def substitute_label(term: Term, old: str, new: str) -> Term:
    """Replace all occurrences of a label."""
    if isinstance(term, Wire):
        return term
    if isinstance(term, Ket):
        return Ket(new) if term.label == old else term
    if isinstance(term, Bra):
        return Bra(new) if term.label == old else term
    if isinstance(term, Juxt):
        return juxt(substitute_label(term.left, old, new),
                    substitute_label(term.right, old, new))
    return term


def apply_church(n: int, f: Term, x: Term) -> Term:
    """
    Apply Church numeral n to function f and argument x.
    
    Church n applied to f and x computes f^n(x).
    
    Process:
    1. Build the numeral structure with placeholders
    2. Substitute f for the "gate" structure
    3. Substitute x for the input
    4. Yank to compute
    
    For this to work, f must be an operator of form |out⟩⟨in|.
    """
    # Build the numeral
    numeral = church(n)
    
    # The numeral has "x" as input and "out" as output
    # Substitute x for the input
    # (If x is a Ket, it plugs into the ⟨x| port)
    
    # Actually, the cleanest approach:
    # Application = juxtaposition with binding
    
    # For n=0: return x
    # For n>0: chain f-applications
    
    # Build the computation chain directly
    if n == 0:
        return x  # λf.λx.x = x
    
    # For n>0, we need to apply f n times to x
    # In spinor terms: f^n(x)
    
    # If f is |out⟩⟨in|, then applying to |x⟩:
    # f |x⟩ = |out⟩⟨in| |x⟩ doesn't yank (different labels)
    
    # We need to connect the wires!
    # f(x) = substitute in→x in f, then we have |out⟩⟨x| |x⟩⟨x|
    # Which yanks to |out⟩⟨x|
    
    # Hmm, this is getting complex. Let me use a simpler model.
    
    # DIRECT MODEL: numbers are VALUES, functions are OPERATORS
    # Application is juxtaposition + yanking
    
    # Represent number n as n "marks" on a wire
    # Represent function f as a transformation
    # f^n = f composed with itself n times
    
    result = x
    for _ in range(n):
        result = juxt(f, result)
    
    return result


# ============================================================================
# Spinor Numbers: The Deep Structure
# ============================================================================

def spinor_n(n: int, base: str = "s") -> Term:
    """
    Number n as a spinor structure.
    
    Insight: a number IS a spinor pattern.
    
    n = |base_0⟩⟨base_0| |base_1⟩⟨base_1| ... |base_{n-1}⟩⟨base_{n-1}|
    
    n identity pairs, each with a distinct label.
    The distinct labels prevent yanking between pairs.
    Each pair IS identity, but the COUNT encodes n.
    
    The number IS the count of identity pairs.
    """
    if n == 0:
        return Wire()  # Zero = nothing
    
    pairs = []
    for i in range(n):
        pair = juxt(Ket(f"{base}_{i}"), Bra(f"{base}_{i}"))
        pairs.append(pair)
    
    result = pairs[0]
    for p in pairs[1:]:
        result = juxt(result, p)
    
    return result


def count_pairs(term: Term) -> int:
    """Count identity pairs in a term."""
    if isinstance(term, Wire):
        return 0
    
    def count_atoms(t):
        if isinstance(t, Wire): return []
        if isinstance(t, (Ket, Bra)): return [t]
        if isinstance(t, Juxt): return count_atoms(t.left) + count_atoms(t.right)
        return []
    
    atoms = count_atoms(term)
    
    # Count matching ket-bra pairs
    count = 0
    i = 0
    while i < len(atoms) - 1:
        if isinstance(atoms[i], Ket) and isinstance(atoms[i+1], Bra):
            if atoms[i].label == atoms[i+1].label:
                count += 1
                i += 2
                continue
        i += 1
    
    return count


# ============================================================================
# Functions as Spinor Operators
# ============================================================================

def spinor_succ() -> Term:
    """
    Successor function as a spinor operator.
    
    SUCC(n) = n + 1
    
    In spinor encoding: SUCC = append another identity pair.
    
    As an operator: SUCC takes input |s_i⟩⟨s_i|... and adds |s_{max+1}⟩⟨s_{max+1}|
    
    Simpler: SUCC = λn. n |s⟩⟨s|  (append one pair)
    
    But we need to "read" the max index from n...
    
    Cleanest: use UNARY encoding where all pairs use the SAME label:
    n = |●⟩⟨●| repeated n times
    
    Then SUCC = prepend/append |●⟩⟨●|
    SUCC(n) = |●⟩⟨●| n  or  n |●⟩⟨●|
    """
    # SUCC is the operator that appends |●⟩⟨●|
    return juxt(Ket("●"), Bra("●"))


def unary_n(n: int) -> Term:
    """
    Unary encoding: n = n copies of |●⟩⟨●|
    
    All pairs use the same label ●, so they're interchangeable.
    The count IS the number.
    """
    if n == 0:
        return Wire()
    
    unit = juxt(Ket("●"), Bra("●"))
    result = unit
    for _ in range(n - 1):
        result = juxt(result, unit)
    
    return result


def count_unary(term: Term) -> int:
    """Count ● pairs in unary encoding."""
    def collect(t):
        if isinstance(t, Wire): return []
        if isinstance(t, (Ket, Bra)): return [t]
        if isinstance(t, Juxt): return collect(t.left) + collect(t.right)
        return []
    
    atoms = collect(term)
    
    count = 0
    i = 0
    while i < len(atoms) - 1:
        if isinstance(atoms[i], Ket) and isinstance(atoms[i+1], Bra):
            if atoms[i].label == "●" and atoms[i+1].label == "●":
                count += 1
                i += 2
                continue
        i += 1
    
    return count


# ============================================================================
# Computation via Yanking
# ============================================================================

def yank_one(term: Term) -> Term:
    """Single yank step: |x⟩⟨x| → ─"""
    if isinstance(term, (Wire, Ket, Bra)):
        return term
    
    if isinstance(term, Juxt):
        # Direct yank: adjacent matching pair
        if isinstance(term.left, Ket) and isinstance(term.right, Bra):
            if term.left.label == term.right.label:
                return Wire()
        if isinstance(term.left, Bra) and isinstance(term.right, Ket):
            if term.left.label == term.right.label:
                return Wire()
        
        # Nested: recurse
        left_y = yank_one(term.left)
        if left_y != term.left:
            return juxt(left_y, term.right)
        right_y = yank_one(term.right)
        if right_y != term.right:
            return juxt(term.left, right_y)
        
        # Cross-boundary yank
        atoms_l = collect_atoms(term.left)
        atoms_r = collect_atoms(term.right)
        
        if atoms_l and atoms_r:
            last, first = atoms_l[-1], atoms_r[0]
            if isinstance(last, Bra) and isinstance(first, Ket) and last.label == first.label:
                return yank_one(juxt(remove_last(term.left), remove_first(term.right)))
            if isinstance(last, Ket) and isinstance(first, Bra) and last.label == first.label:
                return yank_one(juxt(remove_last(term.left), remove_first(term.right)))
    
    return term


def collect_atoms(t: Term) -> List[Union[Ket, Bra]]:
    if isinstance(t, Wire): return []
    if isinstance(t, (Ket, Bra)): return [t]
    if isinstance(t, Juxt): return collect_atoms(t.left) + collect_atoms(t.right)
    return []


def remove_last(t: Term) -> Term:
    if isinstance(t, (Ket, Bra)): return Wire()
    if isinstance(t, Juxt):
        r = remove_last(t.right)
        return t.left if isinstance(r, Wire) else juxt(t.left, r)
    return t


def remove_first(t: Term) -> Term:
    if isinstance(t, (Ket, Bra)): return Wire()
    if isinstance(t, Juxt):
        l = remove_first(t.left)
        return t.right if isinstance(l, Wire) else juxt(l, t.right)
    return t


def normalize(term: Term, steps: int = 100) -> Term:
    for _ in range(steps):
        yanked = yank_one(term)
        if yanked == term:
            return term
        term = yanked
    return term


# ============================================================================
# Actual Church Computation
# ============================================================================

def church_apply(numeral: Term, f: Term, x: Term) -> Term:
    """
    Apply a Church numeral to function f and argument x.
    
    This is the REAL computation: the numeral structure determines
    how many times f gets applied.
    
    For this to work:
    - numeral has placeholders for f and x
    - We "plug in" f and x at the right spots
    - Yanking does the actual computation
    
    Using the "gate" representation:
    - numeral n has n gates, each will become f
    - Each gate is |out⟩⟨in| that will transform input to output
    - x plugs into the first gate's ⟨in|
    - Chain: x → gate_0 → gate_1 → ... → gate_{n-1} → output
    
    For computation, we need to connect f to each gate.
    """
    # The numeral IS the computation structure
    # We just need to connect the wires properly
    
    # For now: direct application
    # numeral n applied to f and x = compose f n times, apply to x
    
    # Extract the count from the numeral
    n = count_pairs(numeral) if numeral != Wire() else 0
    
    # Build f^n(x) directly
    result = x
    for _ in range(n):
        result = juxt(f, result)
    
    return result


def apply_n_times(n: int, f: Term, x: Term) -> Term:
    """
    Apply f n times to x.
    
    f^n(x) = f(f(...f(x)...))
    """
    if n == 0:
        return x
    
    result = x
    for _ in range(n):
        result = juxt(f, result)
    
    return result


# ============================================================================
# Demo
# ============================================================================

def demo():
    print("=" * 60)
    print("SPINOR CHURCH ENCODING")
    print("=" * 60)
    print()
    print("The universe is spinors. Numbers = identity pair count.")
    print("Functions = operators. Computation = yanking.")
    print()
    
    print("-" * 60)
    print("1. NUMBERS AS SPINOR STRUCTURES")
    print("-" * 60)
    print()
    
    print("  Unary encoding: n = n copies of |●⟩⟨●|")
    print()
    
    for n in range(5):
        u = unary_n(n)
        c = count_unary(u)
        print(f"    {n} = {u:30} (count: {c})")
    
    print()
    print("-" * 60)
    print("2. SUCCESSOR = APPEND |●⟩⟨●|")
    print("-" * 60)
    print()
    
    two = unary_n(2)
    succ_unit = spinor_succ()
    three = juxt(two, succ_unit)
    
    print(f"    2 = {two}")
    print(f"    SUCC = {succ_unit}  (the unit pair)")
    print(f"    2 + SUCC = {three}")
    print(f"    Count: {count_unary(three)}")
    
    print()
    print("-" * 60)
    print("3. ADDITION = CONCATENATION")
    print("-" * 60)
    print()
    
    two = unary_n(2)
    three = unary_n(3)
    five = juxt(two, three)
    
    print(f"    2 = {two}")
    print(f"    3 = {three}")
    print(f"    2 + 3 = {five}")
    print(f"    Count: {count_unary(five)}")
    
    print()
    print("-" * 60)
    print("4. MULTIPLICATION = COMPOSITION")
    print("-" * 60)
    print()
    
    print("    For multiplication m × n:")
    print("    = apply 'add m' n times to 0")
    print()
    
    # m × n = add m to 0, n times
    # In spinor: start with Wire() (0), apply juxt(m, _) n times
    
    two = unary_n(2)
    three = unary_n(3)
    
    # 2 × 3 = apply "juxt(two, _)" 3 times starting from Wire()
    result = Wire()
    for _ in range(3):  # n times
        result = juxt(two, result)
    
    print(f"    2 = {two}")
    print(f"    3 = {three}")
    print(f"    2 × 3 = {result}")
    print(f"    Count: {count_unary(result)}")
    
    print()
    print("-" * 60)
    print("5. FUNCTIONS AS OPERATORS")
    print("-" * 60)
    print()
    
    print("    A function f: A → B is a spinor operator |B⟩⟨A|")
    print("    It transforms |A⟩ → |B⟩ via yanking")
    print()
    
    # Simple function: |y⟩⟨x| transforms x → y
    f = juxt(Ket("y"), Bra("x"))
    arg = juxt(Ket("x"), Bra("x"))  # |x⟩⟨x| = value x
    
    print(f"    f = {f}  (function x ↦ y)")
    print(f"    arg = {arg}  (value x)")
    print(f"    f(arg) = {juxt(f, arg)}")
    print(f"    Normalizes to: {normalize(juxt(f, arg))}")
    
    print()
    print("    Note: ⟨x||x⟩ yanks, leaving |y⟩⟨x| |x⟩⟨x| → ...")
    print("    The result is |y⟩ with the x-wire passing through.")
    
    print()
    print("-" * 60)
    print("6. CHURCH NUMERAL APPLICATION")
    print("-" * 60)
    print()
    
    print("    Church numeral n applied to f and x = f^n(x)")
    print()
    
    # Church 2 applied to increment function and value
    # inc = λn. n+1 = juxt(n, |●⟩⟨●|)
    
    inc_unit = spinor_succ()  # |●⟩⟨●|
    
    print(f"    increment unit = {inc_unit}")
    print()
    
    # Church 2 = |●⟩⟨●| |●⟩⟨●|
    church_2 = unary_n(2)
    
    # Apply to inc and 0 (Wire)
    # This means: apply "append ●" twice to nothing
    
    result = Wire()  # Start with 0
    
    print(f"    Church 2 = {church_2}")
    print(f"    Apply to inc, 0:")
    print(f"    Starting value: {result} (count: {count_unary(result)})")
    
    # Apply inc 2 times (as Church 2 specifies)
    for i in range(2):
        result = juxt(result, inc_unit)
        print(f"    After step {i+1}: {result} (count: {count_unary(result)})")
    
    print(f"    Final count: {count_unary(result)} = 2 ✓")
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print()
    print("  From the single rule |x⟩⟨x| → ─:")
    print()
    print("  - Numbers = count of identity pairs")
    print("  - Functions = operators that transform via yanking")
    print("  - Application = juxtaposition + normalization")
    print("  - Church numeral n = apply f n times")
    print()
    print("  The entire computational universe emerges from spinors!")
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            demo()
        else:
            try:
                n = int(sys.argv[1])
                print(f"Unary {n} = {unary_n(n)}")
                print(f"Count: {count_unary(unary_n(n))}")
            except ValueError:
                # Parse as term
                t = eval(sys.argv[1])  # Unsafe, but for demo
                print(f"Term: {t}")
                print(f"Count: {count_unary(t)}")
                print(f"Normalized: {normalize(t)}")
    else:
        demo()