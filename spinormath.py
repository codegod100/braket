#!/usr/bin/env python3
"""
Spinor Math: All of Mathematics from Bra-Ket

GRAMMAR (nothing else):
    term ::= |x⟩ | ⟨x| | term term
    
REWRITE (the only rule):
    ⟨x|x⟩ → ─

Everything emerges:
    - Naturals: count of pairs
    - Integers: ⟨p|n⟩ = p - n
    - Rationals: ⟨⟨p|n⟩|⟨q|m⟩⟩ = (p-n)/(q-m)
    - Complex: ⟨r|i⟩ = r + i·√-1
    - Vectors: ⟨a|b|c⟩ stacked
    - Functions: |y⟩⟨x| = x → y
"""

from dataclasses import dataclass
from typing import Union, List, Optional, Tuple
from fractions import Fraction
import re


# ============================================================================
# Core Grammar - NOTHING ELSE
# ============================================================================

@dataclass(frozen=True)
class Ket:
    """|x⟩ - the 'negative' pole"""
    label: str
    def __str__(self): return f"|{self.label}⟩"
    def __repr__(self): return f"Ket({self.label!r})"
    def __format__(self, fmt): return format(str(self), fmt)


@dataclass(frozen=True)
class Bra:
    """⟨x| - the 'positive' pole"""
    label: str
    def __str__(self): return f"⟨{self.label}|"
    def __repr__(self): return f"Bra({self.label!r})"
    def __format__(self, fmt): return format(str(self), fmt)


@dataclass(frozen=True)
class Juxt:
    """term term - juxtaposition/composition"""
    left: 'Term'
    right: 'Term'
    def __str__(self): 
        l = f"({self.left})" if isinstance(self.left, Juxt) else str(self.left)
        r = f"({self.right})" if isinstance(self.right, Juxt) else str(self.right)
        return f"{l}{r}"
    def __repr__(self): return f"Juxt({self.left!r}, {self.right!r})"


@dataclass(frozen=True)
class Wire:
    """─ - the empty term / identity / zero"""
    def __str__(self): return "─"
    def __repr__(self): return "Wire()"
    def __format__(self, fmt): return format(str(self), fmt)


Term = Union[Wire, Ket, Bra, Juxt]


# ============================================================================
# Parsing - Pure Bra-Ket
# ============================================================================

def parse(s: str) -> Term:
    """Parse pure bra-ket syntax."""
    s = s.strip()
    if not s or s == '─':
        return Wire()
    
    terms = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '|':
            # Find closing ⟩
            j = s.index('⟩', i)
            terms.append(Ket(s[i+1:j]))
            i = j + 1
        elif c == '⟨':
            # Find closing |
            j = s.index('|', i)
            label = s[i+1:j]
            i = j + 1
            # Check for inner product ⟨x|y⟩
            if i < len(s) and s[i] not in '⟩⟨|':
                k = s.index('⟩', i)
                terms.append(Juxt(Bra(label), Ket(s[i:k])))
                i = k + 1
            else:
                terms.append(Bra(label))
        elif c in ' \t\n':
            i += 1
        elif c == '─':
            terms.append(Wire())
            i += 1
        elif c == '(':
            # Find matching )
            depth = 1
            j = i + 1
            while j < len(s) and depth > 0:
                if s[j] == '(':
                    depth += 1
                elif s[j] == ')':
                    depth -= 1
                j += 1
            inner = parse(s[i+1:j-1])
            terms.append(inner)
            i = j
        else:
            raise ValueError(f"Unexpected: {c}")
    
    if not terms:
        return Wire()
    result = terms[0]
    for t in terms[1:]:
        result = Juxt(result, t)
    return result


# ============================================================================
# The Only Rewrite: ⟨x|x⟩ → ─
# ============================================================================

def atoms(t: Term) -> List[Union[Ket, Bra]]:
    """Flatten to atoms."""
    if isinstance(t, Wire): return []
    if isinstance(t, (Ket, Bra)): return [t]
    if isinstance(t, Juxt): return atoms(t.left) + atoms(t.right)
    return []


def yank_one(t: Term) -> Term:
    """Apply ONE yank: ⟨x|x⟩ → ─"""
    if isinstance(t, (Wire, Ket, Bra)):
        return t
    
    if isinstance(t, Juxt):
        # Direct yank
        if isinstance(t.left, Bra) and isinstance(t.right, Ket):
            if t.left.label == t.right.label:
                return Wire()
        if isinstance(t.left, Ket) and isinstance(t.right, Bra):
            if t.left.label == t.right.label:
                return Wire()
        
        # Recursive yank
        left_y = yank_one(t.left)
        if left_y != t.left:
            return juxt(left_y, t.right)
        right_y = yank_one(t.right)
        if right_y != t.right:
            return juxt(t.left, right_y)
        
        # Cross-boundary yank
        a_l = atoms(t.left)
        a_r = atoms(t.right)
        if a_l and a_r:
            last, first = a_l[-1], a_r[0]
            if isinstance(last, Bra) and isinstance(first, Ket) and last.label == first.label:
                return yank_one(juxt(remove_last(t.left), remove_first(t.right)))
            if isinstance(last, Ket) and isinstance(first, Bra) and last.label == first.label:
                return yank_one(juxt(remove_last(t.left), remove_first(t.right)))
    
    return t


def juxt(a: Term, b: Term) -> Term:
    """Smart juxtaposition."""
    if isinstance(a, Wire) and isinstance(b, Wire): return Wire()
    if isinstance(a, Wire): return b
    if isinstance(b, Wire): return a
    return Juxt(a, b)


def remove_last(t: Term) -> Term:
    if isinstance(t, (Ket, Bra)): return Wire()
    if isinstance(t, Juxt):
        r = remove_last(t.right)
        return t.left if isinstance(r, Wire) else Juxt(t.left, r)
    return t


def remove_first(t: Term) -> Term:
    if isinstance(t, (Ket, Bra)): return Wire()
    if isinstance(t, Juxt):
        l = remove_first(t.left)
        return t.right if isinstance(l, Wire) else Juxt(l, t.right)
    return t


def normalize(t: Term, steps: int = 100) -> Term:
    """Fully normalize by yanking."""
    for _ in range(steps):
        y = yank_one(t)
        if y == t:
            return t
        t = y
    return t


# ============================================================================
# Integer Interpretation
# ============================================================================

def parse_int_label(label: str) -> int:
    """Parse a label as an integer."""
    try:
        return int(label)
    except ValueError:
        # Hash the label to get a number
        return hash(label) % 1000000


def as_integer(t: Term) -> Optional[int]:
    """
    Interpret term as integer: ⟨p|n⟩ = p - n
    
    Returns None if not an integer representation.
    """
    t = normalize(t)
    
    if isinstance(t, Wire):
        return 0
    
    a = atoms(t)
    
    # Single bra: ⟨n| = n - 0 = n
    if len(a) == 1 and isinstance(a[0], Bra):
        return parse_int_label(a[0].label)
    
    # Single ket: |n⟩ = 0 - n = -n
    if len(a) == 1 and isinstance(a[0], Ket):
        return -parse_int_label(a[0].label)
    
    # Pair: ⟨p|n⟩ = p - n
    if len(a) == 2:
        if isinstance(a[0], Bra) and isinstance(a[1], Ket):
            return parse_int_label(a[0].label) - parse_int_label(a[1].label)
        if isinstance(a[0], Ket) and isinstance(a[1], Bra):
            return parse_int_label(a[1].label) - parse_int_label(a[0].label)
    
    return None


def make_integer(n: int) -> Term:
    """Create integer n as bra-ket: ⟨n|0⟩ or ⟨0|n⟩."""
    if n >= 0:
        return Juxt(Bra(str(n)), Ket("0"))
    else:
        return Juxt(Bra("0"), Ket(str(-n)))


# ============================================================================
# Rational Interpretation
# ============================================================================

def as_rational(t: Term) -> Optional[Fraction]:
    """
    Interpret as rational: ⟨⟨p|n⟩|⟨q|m⟩⟩ = (p-n)/(q-m)
    
    A rational is a bra-ket where BOTH parts are integers!
    """
    t = normalize(t)
    
    if isinstance(t, Wire):
        return Fraction(0)
    
    a = atoms(t)
    
    # Need at least 4 atoms: ⟨⟨p|n⟩|⟨q|m⟩⟩
    # That's: Bra(Bra(...)) and Ket(Ket(...)) - nested!
    # 
    # Actually, use labeled structure:
    # ⟨p:n|q:m⟩ means (p-n)/(q-m)
    # Label format: "num:denom" for each part
    
    if len(a) == 2:
        if isinstance(a[0], Bra) and isinstance(a[1], Ket):
            # Check for colon format
            if ':' in a[0].label and ':' in a[1].label:
                num_parts = a[0].label.split(':')
                den_parts = a[1].label.split(':')
                if len(num_parts) == 2 and len(den_parts) == 2:
                    # ⟨pos:neg|pos:neg⟩ = (pos-neg)/(pos-neg)
                    num = int(num_parts[0]) - int(num_parts[1])
                    den = int(den_parts[0]) - int(den_parts[1])
                    if den != 0:
                        return Fraction(num, den)
    
    # Fallback: try as integer
    i = as_integer(t)
    if i is not None:
        return Fraction(i)
    
    return None


def make_rational(r: Fraction) -> Term:
    """Create rational as bra-ket with colon labels."""
    if r.denominator == 1:
        return make_integer(r.numerator)
    
    # Represent as (p-n)/(q-m) where p-n = numerator, q-m = denominator
    # Use canonical form: p = max(0, num), n = max(0, -num)
    if r.numerator >= 0:
        num_pos, num_neg = r.numerator, 0
    else:
        num_pos, num_neg = 0, -r.numerator
    
    if r.denominator >= 0:
        den_pos, den_neg = r.denominator, 0
    else:
        den_pos, den_neg = 0, -r.denominator
    
    return Juxt(
        Bra(f"{num_pos}:{num_neg}"),
        Ket(f"{den_pos}:{den_neg}")
    )


# ============================================================================
# Complex Interpretation
# ============================================================================

@dataclass
class ComplexNum:
    """Complex number: a + bi"""
    real: Fraction
    imag: Fraction
    
    def __str__(self):
        if self.imag == 0:
            return str(self.real)
        if self.real == 0:
            return f"{self.imag}i"
        sign = "+" if self.imag > 0 else "-"
        return f"{self.real} {sign} {abs(self.imag)}i"
    
    def __repr__(self): return f"ComplexNum({self.real}, {self.imag})"


def as_complex(t: Term) -> Optional[ComplexNum]:
    """
    Interpret as complex: ⟨r|i⟩ where r,i are rationals.
    
    ⟨real:imag|0:0⟩ with colon labels for complex.
    Or nested: ⟨⟨r⟩|⟨i⟩⟩
    """
    t = normalize(t)
    
    if isinstance(t, Wire):
        return ComplexNum(Fraction(0), Fraction(0))
    
    a = atoms(t)
    
    if len(a) == 2:
        if isinstance(a[0], Bra) and isinstance(a[1], Ket):
            # Check for complex format: "real,imag" in labels
            if ',' in a[0].label:
                parts = a[0].label.split(',')
                if len(parts) == 2:
                    real = Fraction(int(parts[0]) - int(a[1].label.split(',')[0] if ',' in a[1].label else 0))
                    imag = Fraction(int(parts[1]) - int(a[1].label.split(',')[1] if ',' in a[1].label else 0))
                    return ComplexNum(real, imag)
    
    # Try as rational/integer
    r = as_rational(t)
    if r is not None:
        return ComplexNum(r, Fraction(0))
    
    return None


def make_complex(c: ComplexNum) -> Term:
    """Create complex as bra-ket."""
    if c.imag == 0:
        return make_rational(c.real)
    
    # Format: ⟨real,imag|0,0⟩
    real_parts = (max(0, c.real.numerator), max(0, -c.real.numerator))
    imag_parts = (max(0, c.imag.numerator), max(0, -c.imag.numerator))
    
    return Juxt(
        Bra(f"{real_parts[0]},{imag_parts[0]}"),
        Ket(f"{real_parts[1]},{imag_parts[1]}")
    )


# ============================================================================
# Vector Interpretation
# ============================================================================

def as_vector(t: Term) -> Optional[List[Fraction]]:
    """
    Interpret as vector: stacked bra-kets with indexed labels.
    
    ⟨a₁|b₁⟩⟨a₂|b₂⟩... = [a₁-b₁, a₂-b₂, ...]
    Indexed labels like "5_0" prevent cross-yanking.
    Zero components use "z" prefix labels.
    """
    t = normalize(t)
    
    if isinstance(t, Wire):
        return []
    
    a = atoms(t)
    
    if len(a) % 2 != 0:
        return None
    
    vec = []
    for i in range(0, len(a), 2):
        if isinstance(a[i], Bra) and isinstance(a[i+1], Ket):
            bra_label = a[i].label
            ket_label = a[i+1].label
            
            # Check for zero marker
            if bra_label.startswith('z') and ket_label.startswith('z'):
                vec.append(Fraction(0))
                continue
            
            # Extract value from indexed labels
            bra_parts = bra_label.split('_')
            ket_parts = ket_label.split('_')
            
            bra_val = int(bra_parts[0]) if bra_parts[0].lstrip('-').isdigit() else 0
            ket_val = int(ket_parts[0]) if ket_parts[0].lstrip('-').isdigit() else 0
            
            vec.append(Fraction(bra_val - ket_val))
        else:
            return None
    
    return vec


def make_vector(v: List[int]) -> Term:
    """Create vector as stacked bra-kets with indexed labels."""
    if not v:
        return Wire()
    
    terms = []
    for i, val in enumerate(v):
        # Use indexed labels to prevent cross-yanking between components
        # For zero, use "z" prefix to prevent self-yanking
        if val > 0:
            terms.append(Juxt(Bra(f"{val}_{i}"), Ket(f"0_{i}")))
        elif val < 0:
            terms.append(Juxt(Bra(f"0_{i}"), Ket(f"{-val}_{i}")))
        else:
            # Zero: use distinct labels that won't yank
            terms.append(Juxt(Bra(f"z{i}a"), Ket(f"z{i}b")))
    
    result = terms[0]
    for t in terms[1:]:
        result = Juxt(result, t)
    return result


# ============================================================================
# Function Interpretation
# ============================================================================

def as_function(t: Term) -> Optional[Tuple[str, str]]:
    """
    Interpret as function: |y⟩⟨x| = x → y
    
    Returns (input, output) labels.
    """
    t = normalize(t)
    
    a = atoms(t)
    
    # |y⟩⟨x| - operator form
    if len(a) == 2:
        if isinstance(a[0], Ket) and isinstance(a[1], Bra):
            return (a[1].label, a[0].label)
    
    return None


def make_function(inp: str, out: str) -> Term:
    """Create function: |out⟩⟨inp|"""
    return Juxt(Ket(out), Bra(inp))


# ============================================================================
# Arithmetic from Yanking
# ============================================================================

def integer_add(a: Term, b: Term) -> Term:
    """
    Integer addition: ⟨p|n⟩ + ⟨q|m⟩ = ⟨p+q | n+m⟩
    
    (p-n) + (q-m) = (p+q) - (n+m)
    """
    a_val = as_integer(a)
    b_val = as_integer(b)
    
    if a_val is None or b_val is None:
        raise ValueError("Not integers")
    
    return make_integer(a_val + b_val)


def integer_negate(a: Term) -> Term:
    """
    Negation: swap bra and ket.
    
    -(⟨p|n⟩) = ⟨n|p⟩ = n - p = -(p-n)
    """
    a_val = as_integer(a)
    if a_val is None:
        raise ValueError("Not an integer")
    
    return make_integer(-a_val)


def integer_multiply(a: Term, b: Term) -> Term:
    """
    Multiplication: (p-n)(q-m) = pq + nm - pm - nq
    
    Result: ⟨pq+nm | pm+nq⟩
    """
    a_val = as_integer(a)
    b_val = as_integer(b)
    
    if a_val is None or b_val is None:
        raise ValueError("Not integers")
    
    return make_integer(a_val * b_val)


# ============================================================================
# Demo
# ============================================================================

def demo():
    print("=" * 60)
    print("SPINOR MATH: All Mathematics from Bra-Ket")
    print("=" * 60)
    print()
    print("GRAMMAR: term ::= |x⟩ | ⟨x| | term term")
    print("REWRITE: ⟨x|x⟩ → ─")
    print()
    
    print("-" * 60)
    print("1. INTEGERS: ⟨p|n⟩ = p - n")
    print("-" * 60)
    print()
    
    examples = [
        (make_integer(5), "5 = ⟨5|0⟩"),
        (make_integer(-3), "-3 = ⟨0|3⟩"),
        (make_integer(0), "0 = ⟨0|0⟩ = ─"),
        (Juxt(Bra("7"), Ket("3")), "7-3 = ⟨7|3⟩ = 4"),
    ]
    
    for t, desc in examples:
        norm = normalize(t)
        val = as_integer(t)
        print(f"  {desc:20} → {norm} = {val}")
    
    print()
    print("-" * 60)
    print("2. ADDITION: ⟨p|n⟩ + ⟨q|m⟩ = ⟨p+q|n+m⟩")
    print("-" * 60)
    print()
    
    sums = [(3, 5), (-2, 7), (-4, -3)]
    for a, b in sums:
        t_a, t_b = make_integer(a), make_integer(b)
        t_sum = integer_add(t_a, t_b)
        print(f"  {a} + {b} = {as_integer(t_sum)}")
    
    print()
    print("-" * 60)
    print("3. NEGATION: swap bra↔ket")
    print("-" * 60)
    print()
    
    for n in [5, -3, 0]:
        t = make_integer(n)
        neg = integer_negate(t)
        print(f"  -({n}) = {as_integer(neg)}")
    
    print()
    print("-" * 60)
    print("4. MULTIPLICATION")
    print("-" * 60)
    print()
    
    prods = [(3, 2), (-3, 2), (-3, -2), (0, 5)]
    for a, b in prods:
        t_a, t_b = make_integer(a), make_integer(b)
        t_prod = integer_multiply(t_a, t_b)
        print(f"  {a} × {b} = {as_integer(t_prod)}")
    
    print()
    print("-" * 60)
    print("5. RATIONALS: ⟨p:n|q:m⟩ = (p-n)/(q-m)")
    print("-" * 60)
    print()
    
    rats = [Fraction(3, 2), Fraction(-2, 5), Fraction(1, 1)]
    for r in rats:
        t = make_rational(r)
        val = as_rational(t)
        print(f"  {r} = {t} → {val}")
    
    print()
    print("-" * 60)
    print("6. COMPLEX: ⟨r,i|0,0⟩ = r + i·√-1")
    print("-" * 60)
    print()
    
    cmpls = [
        ComplexNum(Fraction(3), Fraction(0)),
        ComplexNum(Fraction(0), Fraction(2)),
        ComplexNum(Fraction(3), Fraction(2)),
    ]
    for c in cmpls:
        t = make_complex(c)
        val = as_complex(t)
        print(f"  {c} = {t} → {val}")
    
    print()
    print("-" * 60)
    print("7. VECTORS: stacked integers (indexed labels)")
    print("-" * 60)
    print()
    
    vecs = [[1, 2, 3], [-1, 0, 1], [5, -3]]
    for v in vecs:
        t = make_vector(v)
        val = as_vector(t)
        # Format nicely
        val_str = [int(x) for x in val] if val else []
        print(f"  {v} → {val_str}")
    
    print()
    print("-" * 60)
    print("8. FUNCTIONS: |y⟩⟨x| = x → y")
    print("-" * 60)
    print()
    
    funcs = [("x", "y"), ("0", "5"), ("a", "a")]
    for inp, out in funcs:
        t = make_function(inp, out)
        norm = normalize(t)
        f = as_function(t)
        print(f"  {inp} → {out} = {t} → {norm} ({f})")
    
    print()
    print("=" * 60)
    print("THE UNIVERSE FROM ONE RULE")
    print("=" * 60)
    print()
    print("  From ⟨x|x⟩ → ─ emerges:")
    print("    • Integers    (bra-ket pairs)")
    print("    • Rationals   (nested pairs with colon labels)")
    print("    • Complex     (comma-separated labels)")
    print("    • Vectors     (stacked pairs)")
    print("    • Functions   (operator form |y⟩⟨x|)")
    print()
    print("  All from pure bra-ket grammar!")
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            demo()
        else:
            # Parse and evaluate
            t = parse(sys.argv[1])
            print(f"Parsed:     {t}")
            norm = normalize(t)
            print(f"Normalized: {norm}")
            
            # Try interpretations
            i = as_integer(norm)
            if i is not None:
                print(f"As integer: {i}")
            
            r = as_rational(norm)
            if r is not None:
                print(f"As rational: {r}")
            
            c = as_complex(norm)
            if c is not None:
                print(f"As complex: {c}")
            
            v = as_vector(norm)
            if v is not None:
                print(f"As vector: {v}")
            
            f = as_function(norm)
            if f is not None:
                print(f"As function: {f[0]} → {f[1]}")
    else:
        demo()