#!/usr/bin/env python3
"""
Spinor Multiplication: Pure Bra-Ket

GRAMMAR: term ::= |x⟩ | ⟨x| | term term
REWRITE: ⟨x|x⟩ → ─

Multiplication emerges from how bra and ket combine:
  Bra × Bra → Bra  (positive × positive = positive)
  Ket × Ket → Bra  (negative × negative = positive!)
  Bra × Ket → Ket  (positive × negative = negative)
  Ket × Bra → Ket  (negative × positive = negative)

For ⟨p|n⟩ × ⟨q|m⟩:
  = (p-n)(q-m)
  = pq - pm - nq + nm
  = (pq + nm) - (pm + nq)
  = ⟨pq+nm | pm+nq⟩

Breaking it down:
  ⟨p| × ⟨q| → ⟨pq|
  |n⟩ × |m⟩ → ⟨nm|
  ⟨p| × |m⟩ → |pm⟩
  |n⟩ × ⟨q| → |nq⟩

Collect: ⟨pq|⟨nm| = ⟨pq+nm|  and  |pm⟩|nq⟩ = |pm+nq⟩
Result: ⟨pq+nm | pm+nq⟩
"""

from dataclasses import dataclass
from typing import Union, List, Tuple, Optional
from functools import reduce


# ============================================================================
# Pure Bra-Ket Grammar
# ============================================================================

@dataclass(frozen=True)
class Ket:
    """|n⟩ - negative pole"""
    value: int
    def __str__(self): return f"|{self.value}⟩"
    def __repr__(self): return f"Ket({self.value})"
    def __format__(self, fmt): return format(str(self), fmt)


@dataclass(frozen=True)
class Bra:
    """⟨n| - positive pole"""
    value: int
    def __str__(self): return f"⟨{self.value}|"
    def __repr__(self): return f"Bra({self.value})"
    def __format__(self, fmt): return format(str(self), fmt)


@dataclass(frozen=True)
class Juxt:
    """term term"""
    left: 'Term'
    right: 'Term'
    def __str__(self):
        l = f"({self.left})" if isinstance(self.left, Juxt) else str(self.left)
        r = f"({self.right})" if isinstance(self.right, Juxt) else str(self.right)
        return f"{l}{r}"
    def __repr__(self): return f"Juxt({self.left!r}, {self.right!r})"


@dataclass(frozen=True)
class Wire:
    """─ - zero / identity"""
    def __str__(self): return "─"
    def __repr__(self): return "Wire()"
    def __format__(self, fmt): return format(str(self), fmt)


Term = Union[Wire, Ket, Bra, Juxt]


def juxt(a: Term, b: Term) -> Term:
    if isinstance(a, Wire) and isinstance(b, Wire): return Wire()
    if isinstance(a, Wire): return b
    if isinstance(b, Wire): return a
    return Juxt(a, b)


# ============================================================================
# Integer as Bra-Ket Pair
# ============================================================================

def make_int(n: int) -> Term:
    """Create integer n as ⟨n|0⟩ or ⟨0|n⟩."""
    if n >= 0:
        return juxt(Bra(n), Ket(0))
    else:
        return juxt(Bra(0), Ket(-n))


def as_int(t: Term) -> Optional[int]:
    """Extract integer from bra-ket pair."""
    if isinstance(t, Wire):
        return 0
    if isinstance(t, Bra):
        return t.value
    if isinstance(t, Ket):
        return -t.value
    if isinstance(t, Juxt):
        l, r = t.left, t.right
        if isinstance(l, Bra) and isinstance(r, Ket):
            return l.value - r.value
        if isinstance(l, Ket) and isinstance(r, Bra):
            return r.value - l.value
    return None


# ============================================================================
# Yanking
# ============================================================================

def atoms(t: Term) -> List[Union[Bra, Ket]]:
    if isinstance(t, Wire): return []
    if isinstance(t, (Bra, Ket)): return [t]
    if isinstance(t, Juxt): return atoms(t.left) + atoms(t.right)
    return []


def yank_one(t: Term) -> Term:
    """Single yank: ⟨n|n⟩ → ─"""
    if isinstance(t, (Wire, Bra, Ket)):
        return t
    
    if isinstance(t, Juxt):
        # Direct yank
        if isinstance(t.left, Bra) and isinstance(t.right, Ket):
            if t.left.value == t.right.value:
                return Wire()
        if isinstance(t.left, Ket) and isinstance(t.right, Bra):
            if t.left.value == t.right.value:
                return Wire()
        
        # Recursive
        left_y = yank_one(t.left)
        if left_y != t.left:
            return juxt(left_y, t.right)
        right_y = yank_one(t.right)
        if right_y != t.right:
            return juxt(t.left, right_y)
        
        # Cross-boundary
        a_l = atoms(t.left)
        a_r = atoms(t.right)
        if a_l and a_r:
            last, first = a_l[-1], a_r[0]
            if isinstance(last, Bra) and isinstance(first, Ket) and last.value == first.value:
                return yank_one(juxt(remove_last(t.left), remove_first(t.right)))
            if isinstance(last, Ket) and isinstance(first, Bra) and last.value == first.value:
                return yank_one(juxt(remove_last(t.left), remove_first(t.right)))
    
    return t


def remove_last(t: Term) -> Term:
    if isinstance(t, (Bra, Ket)): return Wire()
    if isinstance(t, Juxt):
        r = remove_last(t.right)
        return t.left if isinstance(r, Wire) else Juxt(t.left, r)
    return t


def remove_first(t: Term) -> Term:
    if isinstance(t, (Bra, Ket)): return Wire()
    if isinstance(t, Juxt):
        l = remove_first(t.left)
        return t.right if isinstance(l, Wire) else Juxt(l, t.right)
    return t


def normalize(t: Term, steps: int = 100) -> Term:
    for _ in range(steps):
        y = yank_one(t)
        if y == t:
            return t
        t = y
    return t


# ============================================================================
# Pure Bra-Ket Multiplication
# ============================================================================

def multiply_atom(a: Union[Bra, Ket], b: Union[Bra, Ket]) -> Union[Bra, Ket]:
    """
    Multiply single bra or ket atoms.
    
    Bra × Bra → Bra  (+ × + = +)
    Ket × Ket → Bra  (- × - = +)  ← Sign flips!
    Bra × Ket → Ket  (+ × - = -)
    Ket × Bra → Ket  (- × + = -)
    """
    val = a.value * b.value
    
    if isinstance(a, Bra) and isinstance(b, Bra):
        # (+) × (+) = (+)
        return Bra(val)
    elif isinstance(a, Ket) and isinstance(b, Ket):
        # (-) × (-) = (+)
        return Bra(val)
    elif isinstance(a, Bra) and isinstance(b, Ket):
        # (+) × (-) = (-)
        return Ket(val)
    elif isinstance(a, Ket) and isinstance(b, Bra):
        # (-) × (+) = (-)
        return Ket(val)
    else:
        raise ValueError("Invalid atom types")


def collect_positive(atoms: List[Union[Bra, Ket]]) -> int:
    """Sum all positive contributions (Bra values)."""
    return sum(a.value for a in atoms if isinstance(a, Bra))


def collect_negative(atoms: List[Union[Bra, Ket]]) -> int:
    """Sum all negative contributions (Ket values)."""
    return sum(a.value for a in atoms if isinstance(a, Ket))


def multiply_expand(a: Term, b: Term) -> Term:
    """
    Multiply by distributive expansion - PURE BRA-KET!
    
    ⟨p|n⟩ × ⟨q|m⟩ expands to:
      ⟨p| × ⟨q| → ⟨pq|
      ⟨p| × |m⟩ → |pm⟩
      |n⟩ × ⟨q| → |nq⟩
      |n⟩ × |m⟩ → ⟨nm|
    
    Collect:
      Positives: ⟨pq| and ⟨nm| → ⟨pq+nm|
      Negatives: |pm⟩ and |nq⟩ → |pm+nq|
    
    Result: ⟨pq+nm | pm+nq⟩
    """
    atoms_a = atoms(a)
    atoms_b = atoms(b)
    
    if not atoms_a or not atoms_b:
        return Wire()  # Zero × anything = zero
    
    # Expand: cross product of all atoms
    expanded = []
    for atom_a in atoms_a:
        for atom_b in atoms_b:
            expanded.append(multiply_atom(atom_a, atom_b))
    
    # Collect positives and negatives
    pos_val = collect_positive(expanded)
    neg_val = collect_negative(expanded)
    
    # Build result: ⟨pos|neg⟩
    if pos_val == 0 and neg_val == 0:
        return Wire()
    elif pos_val == 0:
        return juxt(Bra(0), Ket(neg_val))
    elif neg_val == 0:
        return juxt(Bra(pos_val), Ket(0))
    else:
        return juxt(Bra(pos_val), Ket(neg_val))


def multiply(a: Term, b: Term) -> Term:
    """Multiply and normalize."""
    result = multiply_expand(a, b)
    return normalize(result)


# ============================================================================
# Step-by-Step Visualization
# ============================================================================

def show_multiply(a: int, b: int) -> None:
    """Show multiplication step by step."""
    print(f"\n{'='*60}")
    print(f"MULTIPLY: {a} × {b}")
    print(f"{'='*60}")
    
    # Create terms
    t_a = make_int(a)
    t_b = make_int(b)
    
    print(f"\nStep 1: Represent as bra-ket pairs")
    print(f"  {a:4} = {t_a}")
    print(f"  {b:4} = {t_b}")
    
    # Get atoms
    atoms_a = atoms(t_a)
    atoms_b = atoms(t_b)
    
    print(f"\nStep 2: Extract atoms")
    print(f"  {t_a} → {atoms_a}")
    print(f"  {t_b} → {atoms_b}")
    
    print(f"\nStep 3: Expand (distributive cross-product)")
    expanded = []
    for atom_a in atoms_a:
        for atom_b in atoms_b:
            prod = multiply_atom(atom_a, atom_b)
            sign = "+" if isinstance(prod, Bra) else "-"
            expanded.append(prod)
            print(f"  {atom_a} × {atom_b} = {prod}  ({sign}{prod.value})")
    
    print(f"\nStep 4: Collect by sign")
    pos = collect_positive(expanded)
    neg = collect_negative(expanded)
    print(f"  Positives (⟨...|): {pos}")
    print(f"  Negatives (|...⟩): {neg}")
    
    print(f"\nStep 5: Build result")
    result = multiply_expand(t_a, t_b)
    print(f"  ⟨{pos}|{neg}⟩ = {result}")
    
    print(f"\nStep 6: Interpret")
    val = as_int(result)
    print(f"  {result} = {val}")
    print(f"\n  {a} × {b} = {val} ✓")


# ============================================================================
# Demo
# ============================================================================

def demo():
    print("=" * 60)
    print("SPINOR MULTIPLICATION: Pure Bra-Ket")
    print("=" * 60)
    print()
    print("The sign rules emerge from bra-ket structure:")
    print()
    print("  ⟨a| × ⟨b| = ⟨ab|   (+) × (+) = (+)")
    print("  |a⟩ × |b⟩ = ⟨ab|   (-) × (-) = (+)  ← SIGN FLIP!")
    print("  ⟨a| × |b⟩ = |ab|   (+) × (-) = (-)")
    print("  |a⟩ × ⟨b| = |ab|   (-) × (+) = (-)")
    print()
    
    # Show individual sign rules
    print("-" * 60)
    print("SIGN RULES")
    print("-" * 60)
    print()
    
    sign_examples = [
        (Bra(3), Bra(2)),   # + × +
        (Ket(3), Ket(2)),   # - × -
        (Bra(3), Ket(2)),   # + × -
        (Ket(3), Bra(2)),   # - × +
    ]
    
    for a, b in sign_examples:
        result = multiply_atom(a, b)
        sign_a = "+" if isinstance(a, Bra) else "-"
        sign_b = "+" if isinstance(b, Bra) else "-"
        sign_r = "+" if isinstance(result, Bra) else "-"
        print(f"  {a} × {b} = {result}   ({sign_a}) × ({sign_b}) = ({sign_r})")
    
    # Show full multiplications
    print()
    print("-" * 60)
    print("INTEGER MULTIPLICATION")
    print("-" * 60)
    
    examples = [
        (3, 2),     # + × +
        (-3, 2),    # - × +
        (3, -2),    # + × -
        (-3, -2),   # - × -
        (0, 5),     # 0 × +
        (4, 0),     # + × 0
    ]
    
    for a, b in examples:
        show_multiply(a, b)
    
    print()
    print("=" * 60)
    print("THE KEY INSIGHT")
    print("=" * 60)
    print()
    print("  Multiplication signs emerge from bra-ket structure!")
    print()
    print("  Bra = positive pole    Ket = negative pole")
    print()
    print("  When you multiply them:")
    print("    - Same poles (both bra or both ket) → Bra (positive)")
    print("    - Different poles → Ket (negative)")
    print()
    print("  This is WHY (-) × (-) = (+)!")
    print("  The spinor structure FORCES the sign flip.")
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            demo()
        elif len(sys.argv) == 3:
            # Multiply two numbers
            a, b = int(sys.argv[1]), int(sys.argv[2])
            t_a, t_b = make_int(a), make_int(b)
            result = multiply(t_a, t_b)
            val = as_int(result)
            print(f"{a} × {b} = {val}")
            print(f"{t_a} × {t_b} = {result}")
    else:
        demo()