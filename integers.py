#!/usr/bin/env python3
"""
Spinor Integers: Bra-Ket as the Grothendieck Construction

The integers ℤ are constructed from naturals ℕ via:
  - Pairs (p, n) representing p - n
  - Equivalence: (a, b) ~ (c, d) iff a + d = b + c

In bra-ket:
  ⟨p|n⟩ represents the integer p - n
  
  ⟨5|2⟩ = +3   (positive)
  ⟨2|5⟩ = -3   (negative)
  ⟨x|x⟩ = 0    (zero, yanks to wire)

The yanking rule IS the equivalence relation:
  ⟨x|x⟩ ~ ⟨0|0⟩ ~ ─   (all represent zero)

This gives us:
  - Positive integers: ⟨n|0⟩ = n
  - Negative integers: ⟨0|n⟩ = -n
  - Zero: ⟨x|x⟩ = 0
  - Addition: (⟨a|b⟩) + (⟨c|d⟩) = ⟨a+c | b+d⟩

The universe IS spinor arithmetic!
"""

from dataclasses import dataclass
from typing import Union, Tuple


# ============================================================================
# Terms
# ============================================================================

@dataclass(frozen=True)
class Ket:
    """Ket |n⟩ represents the 'negative' part of an integer pair"""
    value: int
    def __str__(self): return f"|{self.value}⟩"
    def __repr__(self): return f"Ket({self.value})"


@dataclass(frozen=True)
class Bra:
    """Bra ⟨n| represents the 'positive' part of an integer pair"""
    value: int
    def __str__(self): return f"⟨{self.value}|"
    def __repr__(self): return f"Bra({self.value})"


@dataclass(frozen=True)
class Pair:
    """Integer as a bra-ket pair: ⟨p|n⟩ = p - n"""
    pos: int  # positive part (bra)
    neg: int  # negative part (ket)
    
    def __str__(self): return f"⟨{self.pos}|{self.neg}⟩"
    def __repr__(self): return f"Pair({self.pos}, {self.neg})"
    def __format__(self, fmt): return format(str(self), fmt)
    
    def to_int(self) -> int:
        """Compute the integer value: p - n"""
        return self.pos - self.neg
    
    def normalize(self) -> 'Pair':
        """Normalize to canonical form (reduce by common part)"""
        # ⟨a|b⟩ ~ ⟨a-min(a,b) | b-min(a,b)⟩
        m = min(self.pos, self.neg)
        if m == 0:
            return self
        return Pair(self.pos - m, self.neg - m)
    
    def is_zero(self) -> bool:
        """Check if this represents zero"""
        return self.pos == self.neg


@dataclass(frozen=True)
class Wire:
    """Zero / identity"""
    def __str__(self): return "─"
    def __repr__(self): return "Wire()"


Term = Union[Wire, Ket, Bra, Pair]


# ============================================================================
# Integer Operations
# ============================================================================

def make_int(n: int) -> Pair:
    """Create an integer as a bra-ket pair.
    
    Positive: ⟨n|0⟩
    Negative: ⟨0|n⟩
    Zero:     ⟨0|0⟩ = ─
    """
    if n >= 0:
        return Pair(n, 0)
    else:
        return Pair(0, -n)


def add_int(a: Pair, b: Pair) -> Pair:
    """Add two integers: (p1-n1) + (p2-n2) = (p1+p2) - (n1+n2)"""
    return Pair(a.pos + b.pos, a.neg + b.neg)


def negate_int(a: Pair) -> Pair:
    """Negate: -(p-n) = n-p"""
    return Pair(a.neg, a.pos)


def subtract_int(a: Pair, b: Pair) -> Pair:
    """Subtract: a - b = a + (-b)"""
    return add_int(a, negate_int(b))


def multiply_int(a: Pair, b: Pair) -> Pair:
    """
    Multiply: (p1-n1) × (p2-n2)
    
    Using the distributive law:
    = p1·p2 - p1·n2 - n1·p2 + n1·n2
    = (p1·p2 + n1·n2) - (p1·n2 + n1·p2)
    """
    pos = a.pos * b.pos + a.neg * b.neg
    neg = a.pos * b.neg + a.neg * b.pos
    return Pair(pos, neg)


# ============================================================================
# Yanking as Equivalence
# ============================================================================

def yank(pair: Pair) -> Union[Pair, Wire]:
    """
    Yank: reduce ⟨a|b⟩ by subtracting common part.
    
    This IS the equivalence relation!
    ⟨a|b⟩ ~ ⟨a-c | b-c⟩ for any c ≤ min(a,b)
    
    If a = b, the result is ⟨0|0⟩ = zero = wire.
    """
    normalized = pair.normalize()
    
    if normalized.is_zero():
        return Wire()
    
    return normalized


# ============================================================================
# Demo
# ============================================================================

def demo():
    print("=" * 60)
    print("SPINOR INTEGERS: Bra-Ket as Grothendieck Construction")
    print("=" * 60)
    print()
    
    print("The Grothendieck construction:")
    print("  Integer = pair (p, n) of naturals")
    print("  Meaning: p - n")
    print("  Equivalence: (a,b) ~ (c,d) iff a+d = b+c")
    print()
    
    print("In bra-ket:")
    print("  ⟨p|n⟩ = (p, n) = p - n")
    print("  ⟨p|p⟩ = 0  →  yanks to wire")
    print()
    
    print("-" * 60)
    print("1. INTEGERS FROM BRA-KET")
    print("-" * 60)
    print()
    
    for n in [-3, -1, 0, 1, 3, 5]:
        p = make_int(n)
        print(f"  {n:3} = {p:12} = {p.to_int():3}")
    
    print()
    print("-" * 60)
    print("2. YANKING = EQUIVALENCE")
    print("-" * 60)
    print()
    
    examples = [
        Pair(5, 5),   # Zero
        Pair(7, 3),   # +4
        Pair(2, 6),   # -4
        Pair(10, 10), # Zero (bigger)
    ]
    
    for p in examples:
        y = yank(p)
        print(f"  {p} = {p.to_int():3}  →  {y}")
    
    print()
    print("-" * 60)
    print("3. ADDITION")
    print("-" * 60)
    print()
    
    pairs = [
        (make_int(3), make_int(2)),
        (make_int(-3), make_int(2)),
        (make_int(5), make_int(-7)),
    ]
    
    for a, b in pairs:
        result = add_int(a, b)
        y = yank(result)
        print(f"  {a.to_int():3} + {b.to_int():3} = {result}  →  {y} = {result.to_int()}")
    
    print()
    print("-" * 60)
    print("4. NEGATION")
    print("-" * 60)
    print()
    
    for n in [3, -3, 0]:
        p = make_int(n)
        neg = negate_int(p)
        print(f"  -({p}) = {neg} = {neg.to_int()}")
    
    print()
    print("-" * 60)
    print("5. SUBTRACTION")
    print("-" * 60)
    print()
    
    pairs = [
        (make_int(5), make_int(3)),
        (make_int(3), make_int(5)),
        (make_int(-2), make_int(-5)),
    ]
    
    for a, b in pairs:
        result = subtract_int(a, b)
        y = yank(result)
        print(f"  {a.to_int():3} - {b.to_int():3} = {result}  →  {y} = {result.to_int()}")
    
    print()
    print("-" * 60)
    print("6. MULTIPLICATION")
    print("-" * 60)
    print()
    
    pairs = [
        (make_int(3), make_int(2)),
        (make_int(-3), make_int(2)),
        (make_int(-3), make_int(-2)),
        (make_int(0), make_int(5)),
    ]
    
    for a, b in pairs:
        result = multiply_int(a, b)
        y = yank(result)
        print(f"  {a.to_int():3} × {b.to_int():3} = {result.normalize()}  = {result.to_int()}")
    
    print()
    print("=" * 60)
    print("THE KEY INSIGHT")
    print("=" * 60)
    print()
    print("  Bra ⟨n| = positive n (in the 'positive' slot)")
    print("  Ket |n⟩ = negative n (in the 'negative' slot)")
    print()
    print("  ⟨p|n⟩ = (p, n) = p - n = an integer!")
    print()
    print("  Yanking: ⟨x|x⟩ → ─ is the SAME as saying (x,x) ~ (0,0)")
    print("  Both represent zero!")
    print()
    print("  The entire ring of integers ℤ emerges from:")
    print("    - Bra-ket pairs")
    print("    - The yanking equivalence")
    print()


if __name__ == "__main__":
    demo()