#!/usr/bin/env python3
"""
Spinor Division: Pure Bra-Ket

GRAMMAR: term ::= |x⟩ | ⟨x| | term term
REWRITE: ⟨x|x⟩ → ─

Division = multiplication by inverse

For integers:
  a ÷ b = a × b⁻¹

The inverse of ⟨q|m⟩ = 1/(q-m)
This is a RATIONAL, represented as nested bra-ket:
  ⟨⟨1|0⟩|⟨q-m|0⟩⟩

For rationals (using colon notation):
  ⟨p:n|q:m⟩ = (p-n)/(q-m)
  
  Inverse: ⟨q:m|p:n⟩ (swap numerator and denominator!)
  
Division of rationals:
  ⟨a:b|c:d⟩ ÷ ⟨e:f|g:h⟩
  = ⟨a:b|c:d⟩ × ⟨g:h|e:f⟩
  = (a-b)/(c-d) × (g-h)/(e-f)
  = ⟨(a-b)(g-h):(c-d)(e-f)⟩

Division by zero: UNDEFINED (no inverse)
"""

from dataclasses import dataclass
from typing import Union, List, Optional, Tuple
from fractions import Fraction


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
# Integers
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
        val = t.value
        if isinstance(val, int):
            return val
        if isinstance(val, str) and ':' not in val:
            try:
                return int(val)
            except ValueError:
                return None
        return None
    if isinstance(t, Ket):
        val = t.value
        if isinstance(val, int):
            return -val
        if isinstance(val, str) and ':' not in val:
            try:
                return -int(val)
            except ValueError:
                return None
        return None
    if isinstance(t, Juxt):
        l, r = t.left, t.right
        if isinstance(l, Bra) and isinstance(r, Ket):
            l_val = l.value if isinstance(l.value, int) else 0
            r_val = r.value if isinstance(r.value, int) else 0
            # Only return integer if both are integers (no colons)
            if isinstance(l.value, str) or isinstance(r.value, str):
                return None  # It's a rational, not an integer
            return l_val - r_val
        if isinstance(l, Ket) and isinstance(r, Bra):
            l_val = l.value if isinstance(l.value, int) else 0
            r_val = r.value if isinstance(r.value, int) else 0
            if isinstance(l.value, str) or isinstance(r.value, str):
                return None
            return r_val - l_val
    return None


# ============================================================================
# Rationals (Colon Notation)
# ============================================================================

def make_rational(num: int, den: int) -> Term:
    """
    Create rational as ⟨num_pos:num_neg|den_pos:den_neg⟩
    
    where num = num_pos - num_neg, den = den_pos - den_neg
    
    Simplified: ⟨num|den⟩ where we track both as integers
    Using colon to separate: ⟨num:0|den:0⟩ for positive den
    """
    if den == 0:
        raise ValueError("Division by zero!")
    
    # Reduce to lowest terms
    from math import gcd
    g = gcd(abs(num), abs(den))
    if g > 1:
        num //= g
        den //= g
    
    # Keep denominator positive by moving sign to numerator
    if den < 0:
        num = -num
        den = -den
    
    # Represent as ⟨num:0|den:0⟩
    return juxt(Bra(f"{num}:0"), Ket(f"{den}:0"))


def as_rational(t: Term) -> Optional[Fraction]:
    """Extract rational from bra-ket.
    
    For integer form ⟨p|n⟩: returns Fraction(p-n)
    For rational form ⟨p:n|q:m⟩: returns Fraction(p-n, q-m)
    """
    if isinstance(t, Wire):
        return Fraction(0)
    
    if isinstance(t, Bra):
        label = t.value
        if isinstance(label, str) and ':' in label:
            parts = label.split(':')
            return Fraction(int(parts[0]) - int(parts[1]))
        return Fraction(label if isinstance(label, int) else 0)
    
    if isinstance(t, Ket):
        label = t.value
        if isinstance(label, str) and ':' in label:
            parts = label.split(':')
            return Fraction(int(parts[1]) - int(parts[0]))
        return Fraction(-(label if isinstance(label, int) else 0))
    
    if isinstance(t, Juxt):
        l, r = t.left, t.right
        
        if isinstance(l, Bra) and isinstance(r, Ket):
            l_label = l.value
            r_label = r.value
            
            # Check for colon notation (rational)
            is_rational = (isinstance(l_label, str) and ':' in l_label and
                          isinstance(r_label, str) and ':' in r_label)
            
            if is_rational:
                # Both have colon: it's a rational a/b
                l_parts = l_label.split(':')
                r_parts = r_label.split(':')
                num = int(l_parts[0]) - int(l_parts[1])
                den = int(r_parts[0]) - int(r_parts[1])
                if den == 0:
                    return None  # Undefined
                return Fraction(num, den)
            else:
                # It's an integer
                l_val = l_label if isinstance(l_label, int) else 0
                r_val = r_label if isinstance(r_label, int) else 0
                return Fraction(l_val - r_val)
    
    # Try as integer
    i = as_int(t)
    if i is not None:
        return Fraction(i)
    
    return None


# ============================================================================
# Inverse
# ============================================================================

def inverse(t: Term) -> Term:
    """
    Compute multiplicative inverse.
    
    For integer ⟨p|n⟩:
      Inverse = 1/(p-n) = ⟨1|p-n⟩ as rational
    
    For rational ⟨p:n|q:m⟩ = (p-n)/(q-m):
      Inverse = ⟨q:m|p:n⟩ = (q-m)/(p-n) = SWAP!
    
    Zero has no inverse (division by zero undefined).
    """
    # Check for zero
    val = as_int(t)
    if val == 0:
        raise ValueError("Division by zero: zero has no inverse!")
    
    # Check for rational
    rat = as_rational(t)
    if rat is None:
        raise ValueError("Cannot compute inverse")
    
    # Inverse = 1/rat
    inv = Fraction(1) / rat
    
    # Build rational term
    return make_rational(inv.numerator, inv.denominator)


# ============================================================================
# Multiplication (for reference)
# ============================================================================

def multiply_atom(a: Union[Bra, Ket], b: Union[Bra, Ket]) -> Union[Bra, Ket]:
    """Multiply single atoms."""
    # Extract values
    a_val = a.value if isinstance(a.value, int) else 0
    b_val = b.value if isinstance(b.value, int) else 0
    
    # Handle colon notation
    if isinstance(a.value, str) and ':' in a.value:
        parts = a.value.split(':')
        a_val = int(parts[0]) - int(parts[1])
    if isinstance(b.value, str) and ':' in b.value:
        parts = b.value.split(':')
        b_val = int(parts[0]) - int(parts[1])
    
    val = a_val * b_val
    
    # Sign rules
    if isinstance(a, Bra) and isinstance(b, Bra):
        return Bra(val)
    elif isinstance(a, Ket) and isinstance(b, Ket):
        return Bra(val)
    elif isinstance(a, Bra) and isinstance(b, Ket):
        return Ket(val)
    elif isinstance(a, Ket) and isinstance(b, Bra):
        return Ket(val)
    else:
        raise ValueError("Invalid atoms")


def multiply_rational(a: Term, b: Term) -> Term:
    """Multiply two rationals."""
    r_a = as_rational(a)
    r_b = as_rational(b)
    
    if r_a is None or r_b is None:
        raise ValueError("Not rationals")
    
    result = r_a * r_b
    return make_rational(result.numerator, result.denominator)


# ============================================================================
# Division
# ============================================================================

def divide(a: Term, b: Term) -> Term:
    """
    Division: a ÷ b = a × b⁻¹
    
    For integers:
      ⟨p|n⟩ ÷ ⟨q|m⟩ = ⟨p|n⟩ × inverse(⟨q|m⟩)
                    = (p-n) × 1/(q-m)
                    = (p-n)/(q-m)
    
    For rationals:
      ⟨a:b|c:d⟩ ÷ ⟨e:f|g:h⟩ = ⟨a:b|c:d⟩ × inverse(⟨e:f|g:h⟩)
                            = ⟨a:b|c:d⟩ × ⟨g:h|e:f⟩
    """
    b_inv = inverse(b)
    return multiply_rational(a, b_inv)


# ============================================================================
# Step-by-Step Visualization
# ============================================================================

def show_division(a: int, b: int) -> None:
    """Show division step by step."""
    print(f"\n{'='*60}")
    print(f"DIVISION: {a} ÷ {b}")
    print(f"{'='*60}")
    
    if b == 0:
        print(f"\n  ERROR: Division by zero!")
        print(f"  Zero has no inverse in the spinor framework.")
        return
    
    # Create terms
    t_a = make_int(a)
    t_b = make_int(b)
    
    print(f"\nStep 1: Represent as bra-ket pairs")
    print(f"  {a:4} = {t_a}")
    print(f"  {b:4} = {t_b}")
    
    print(f"\nStep 2: Compute inverse of divisor")
    print(f"  inverse({t_b}) = inverse({as_int(t_b)})")
    t_inv = inverse(t_b)
    r_inv = as_rational(t_inv)
    print(f"  = 1/{b} = {r_inv}")
    print(f"  = {t_inv}")
    
    print(f"\nStep 3: Multiply dividend by inverse")
    result = divide(t_a, t_b)
    r_result = as_rational(result)
    print(f"  {t_a} × {t_inv}")
    print(f"  = {a} × 1/{b}")
    print(f"  = {a}/{b}")
    print(f"  = {r_result}")
    
    print(f"\nStep 4: Verify")
    print(f"  {r_result} × {b} = {r_result * b}")
    print(f"  {a} ÷ {b} = {r_result} ✓")


def show_rational_division(a: Tuple[int, int], b: Tuple[int, int]) -> None:
    """Show division of two rationals."""
    print(f"\n{'='*60}")
    print(f"RATIONAL DIVISION: {a[0]}/{a[1]} ÷ {b[0]}/{b[1]}")
    print(f"{'='*60}")
    
    t_a = make_rational(a[0], a[1])
    t_b = make_rational(b[0], b[1])
    r_a = as_rational(t_a)
    r_b = as_rational(t_b)
    
    print(f"\nStep 1: Represent as bra-ket")
    print(f"  {a[0]}/{a[1]} = {t_a} = {r_a}")
    print(f"  {b[0]}/{b[1]} = {t_b} = {r_b}")
    
    print(f"\nStep 2: Compute inverse")
    t_inv = inverse(t_b)
    r_inv = as_rational(t_inv)
    print(f"  inverse({t_b}) = {t_inv}")
    print(f"  = {r_inv}")
    print(f"  (Swap numerator and denominator!)")
    
    print(f"\nStep 3: Multiply")
    result = divide(t_a, t_b)
    r_result = as_rational(result)
    print(f"  {r_a} × {r_inv} = {r_result}")
    print(f"  {a[0]}/{a[1]} ÷ {b[0]}/{b[1]} = {r_result} ✓")


# ============================================================================
# Demo
# ============================================================================

def demo():
    print("=" * 60)
    print("SPINOR DIVISION: Pure Bra-Ket")
    print("=" * 60)
    print()
    print("Division = Multiplication by Inverse")
    print()
    print("For rational ⟨num:0|den:0⟩:")
    print("  Inverse = ⟨den:0|num:0⟩")
    print("  (SWAP bra and ket!)")
    print()
    print("Division by zero: UNDEFINED")
    print("  Zero has no inverse - it annihilates everything!")
    print()
    
    print("-" * 60)
    print("INTEGER DIVISION (creates rationals)")
    print("-" * 60)
    
    examples = [
        (6, 2),     # Exact
        (7, 2),     # Fraction
        (1, 3),     # Small fraction
        (-6, 2),    # Negative/positive
        (6, -2),    # Positive/negative
        (-6, -2),   # Negative/negative
        (0, 5),     # Zero divided
        (5, 0),     # Division by zero
    ]
    
    for a, b in examples:
        show_division(a, b)
    
    print()
    print("-" * 60)
    print("RATIONAL DIVISION")
    print("-" * 60)
    
    rat_examples = [
        ((1, 2), (1, 4)),    # 1/2 ÷ 1/4 = 2
        ((3, 4), (2, 3)),    # 3/4 ÷ 2/3 = 9/8
        ((2, 5), (1, 10)),   # 2/5 ÷ 1/10 = 4
    ]
    
    for a, b in rat_examples:
        show_rational_division(a, b)
    
    print()
    print("=" * 60)
    print("THE KEY INSIGHT")
    print("=" * 60)
    print()
    print("  Division takes us from integers to rationals!")
    print()
    print("  For ⟨num|den⟩, the inverse is:")
    print("    1/(num/den) = den/num = ⟨den|num⟩")
    print()
    print("  SWAP bra and ket for the inverse!")
    print()
    print("  Division by zero is undefined because:")
    print("    ⟨0|0⟩ = 0, and there's no term whose")
    print("    product with 0 is 1 (non-zero annihilates)")
    print()
    print("  The spinor structure naturally shows why")
    print("  division by zero is impossible!")
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            demo()
        elif len(sys.argv) == 3:
            a, b = int(sys.argv[1]), int(sys.argv[2])
            try:
                t_a, t_b = make_int(a), make_int(b)
                result = divide(t_a, t_b)
                r = as_rational(result)
                print(f"{a} ÷ {b} = {r}")
                print(f"{t_a} ÷ {t_b} = {result}")
            except ValueError as e:
                print(f"ERROR: {e}")
    else:
        demo()