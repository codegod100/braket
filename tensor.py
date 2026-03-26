#!/usr/bin/env python3
"""
Spinor Tensor Calculus: Pure Bra-Ket

GRAMMAR: term ::= |x⟩ | ⟨x| | term term
REWRITE: ⟨x|x⟩ → ─

Tensors are the NATURAL STRUCTURE of bra-ket:
  
  Vector (rank-1, contravariant):     |v⟩ = ket
  Covector (rank-1, covariant):       ⟨v| = bra
  Scalar (rank-0):                    ⟨v|w⟩ or ─
  Operator (rank-2):                  |v⟩⟨w|
  Matrix (rank-2):                    Σᵢⱼ |eᵢ⟩⟨eⱼ|
  
Tensor product: juxtaposition
  |a⟩ ⊗ |b⟩ = |a⟩|b⟩ = |ab⟩ (multi-index)
  
Contraction: yanking
  ⟨x|x⟩ → ─  (trace over matching indices)
  
Index raising/lowering: swap bra ↔ ket
  |v⟩⁺ = ⟨v|    (adjoint)
  ⟨v|⁺ = |v⟩

This is EXACTLY Dirac notation - which IS tensor calculus!
"""

from dataclasses import dataclass
from typing import Union, List, Optional, Tuple, Dict
from fractions import Fraction
import re


# ============================================================================
# Pure Bra-Ket Grammar with Tensor Indices
# ============================================================================

@dataclass(frozen=True)
class Index:
    """Tensor index with optional variance."""
    name: str
    variance: str = "upper"  # "upper" (contravariant) or "lower" (covariant)
    
    def __str__(self):
        if self.variance == "upper":
            return self.name
        else:
            return f"_{self.name}"
    
    def __repr__(self): return f"Index({self.name}, {self.variance})"
    def __hash__(self): return hash((self.name, self.variance))
    def __eq__(self, other):
        if not isinstance(other, Index):
            return False
        return self.name == other.name and self.variance == other.variance


@dataclass(frozen=True)
class Ket:
    """|vᵢ⟩ - contravariant vector (upper index)"""
    label: str
    index: Optional[Index] = None
    
    def __str__(self):
        if self.index:
            return f"|{self.label}{self.index}|⟩"
        return f"|{self.label}⟩"
    
    def __repr__(self): return f"Ket({self.label!r}, {self.index!r})"
    def __format__(self, fmt): return format(str(self), fmt)


@dataclass(frozen=True)
class Bra:
    """⟨vⁱ| - covariant vector (lower index)"""
    label: str
    index: Optional[Index] = None
    
    def __str__(self):
        if self.index:
            return f"⟨{self.label}{self.index}||"
        return f"⟨{self.label}||"
    
    def __repr__(self): return f"Bra({self.label!r}, {self.index!r})"
    def __format__(self, fmt): return format(str(self), fmt)


@dataclass(frozen=True)
class Juxt:
    """Tensor product: term ⊗ term"""
    left: 'Term'
    right: 'Term'
    
    def __str__(self):
        l = f"({self.left})" if isinstance(self.left, Juxt) else str(self.left)
        r = f"({self.right})" if isinstance(self.right, Juxt) else str(self.right)
        return f"{l} ⊗ {r}"
    
    def __repr__(self): return f"Juxt({self.left!r}, {self.right!r})"
    def __format__(self, fmt): return format(str(self), fmt)


@dataclass(frozen=True)
class Wire:
    """─ - zero / identity / scalar"""
    def __str__(self): return "─"
    def __repr__(self): return "Wire()"
    def __format__(self, fmt): return format(str(self), fmt)


Term = Union[Wire, Ket, Bra, Juxt]


def tensor(a: Term, b: Term) -> Term:
    """Tensor product (juxtaposition)."""
    if isinstance(a, Wire): return b
    if isinstance(b, Wire): return a
    return Juxt(a, b)


# ============================================================================
# Tensor Operations
# ============================================================================

def outer_product(v_ket: Ket, w_bra: Bra) -> Term:
    """
    Outer product: |v⟩⟨w| = rank-2 operator/matrix
    
    This is the tensor product of a vector and covector.
    In index notation: vⁱ wⱼ (no contraction)
    """
    return tensor(v_ket, w_bra)


def inner_product(v_bra: Bra, w_ket: Ket) -> Term:
    """
    Inner product: ⟨v|w⟩ = scalar
    
    Contraction over matching index.
    In index notation: vᵢ wⁱ (sum over i)
    """
    return tensor(v_bra, w_ket)


def contract(term: Term) -> Term:
    """
    Contract all matching indices (Einstein summation).
    
    Repeated index = contraction:
      ⟨eᵢ|eᵢ⟩ → ─  (trace)
    
    This IS the yanking rule with tensor indices!
    """
    if isinstance(term, (Wire, Ket, Bra)):
        return term
    
    if isinstance(term, Juxt):
        # Check for matching bra-ket pair
        left_atoms = flatten(term.left)
        right_atoms = flatten(term.right)
        
        if left_atoms and right_atoms:
            last_left = left_atoms[-1]
            first_right = right_atoms[0]
            
            # Check for contraction: matching indices
            if isinstance(last_left, Bra) and isinstance(first_right, Ket):
                if (last_left.index and first_right.index and
                    last_left.index.name == first_right.index.name):
                    # Contraction! Apply yanking.
                    new_left = remove_last(term.left)
                    new_right = remove_first(term.right)
                    return contract(tensor(new_left, new_right))
            
            if isinstance(last_left, Ket) and isinstance(first_right, Bra):
                if (last_left.index and first_right.index and
                    last_left.index.name == first_right.index.name):
                    new_left = remove_last(term.left)
                    new_right = remove_first(term.right)
                    return contract(tensor(new_left, new_right))
        
        # Recursive contraction
        left_c = contract(term.left)
        right_c = contract(term.right)
        if left_c != term.left or right_c != term.right:
            return contract(tensor(left_c, right_c))
        
        return term
    
    return term


def flatten(term: Term) -> List[Union[Bra, Ket]]:
    """Flatten to list of atoms."""
    if isinstance(term, Wire): return []
    if isinstance(term, (Bra, Ket)): return [term]
    if isinstance(term, Juxt): return flatten(term.left) + flatten(term.right)
    return []


def remove_last(term: Term) -> Term:
    """Remove last atom from term."""
    if isinstance(term, (Bra, Ket)): return Wire()
    if isinstance(term, Juxt):
        r = remove_last(term.right)
        if isinstance(r, Wire): return term.left
        return Juxt(term.left, r)
    return term


def remove_first(term: Term) -> Term:
    """Remove first atom from term."""
    if isinstance(term, (Bra, Ket)): return Wire()
    if isinstance(term, Juxt):
        l = remove_first(term.left)
        if isinstance(l, Wire): return term.right
        return Juxt(l, term.right)
    return term


# ============================================================================
# Adjoint / Transpose
# ============================================================================

def adjoint(term: Term) -> Term:
    """
    Hermitian adjoint: swap bra ↔ ket, reverse order.
    
    (|v⟩)† = ⟨v|
    (⟨v|)† = |v⟩
    (|a⟩⟨b|)† = |b⟩⟨a|
    (A ⊗ B)† = B† ⊗ A†
    """
    if isinstance(term, Wire):
        return term
    if isinstance(term, Ket):
        return Bra(term.label, Index(term.index.name, "lower") if term.index else None)
    if isinstance(term, Bra):
        return Ket(term.label, Index(term.index.name, "upper") if term.index else None)
    if isinstance(term, Juxt):
        # Reverse order and adjoint each part
        return tensor(adjoint(term.right), adjoint(term.left))
    return term


def transpose(term: Term) -> Term:
    """
    Transpose: swap bra ↔ ket, reverse order.
    (Same as adjoint for real labels)
    """
    return adjoint(term)


# ============================================================================
# Trace
# ============================================================================

def trace(term: Term) -> Term:
    """
    Trace: contract matching indices.
    
    Tr(|v⟩⟨w|) = ⟨w|v⟩
    Tr(A ⊗ B) = Tr(A) × Tr(B)
    """
    return contract(term)


# ============================================================================
# Matrix Representation
# ============================================================================

def matrix_from_terms(terms: List[Tuple[Ket, Bra]]) -> Term:
    """
    Build matrix from outer products.
    
    M = Σᵢⱼ mᵢⱼ |eᵢ⟩⟨eⱼ|
    
    Where eᵢ are basis vectors.
    """
    result = Wire()
    for ket, bra in terms:
        result = tensor(result, outer_product(ket, bra))
    return result


def apply_operator(op: Term, vec: Ket) -> Term:
    """
    Apply operator to vector.
    
    (|v⟩⟨w|)|x⟩ = |v⟩⟨w|x⟩ = |v⟩⟨w|x⟩
    
    If w = x, this contracts to |v⟩.
    """
    product = tensor(op, vec)
    return contract(product)


# ============================================================================
# Metric Tensor (Index Raising/Lowering)
# ============================================================================

def raise_index(bra: Bra, metric: Dict[str, Dict[str, Fraction]]) -> Ket:
    """
    Raise index using metric tensor gⁱʲ.
    
    vⁱ = gⁱʲ vⱼ
    
    In bra-ket: ⟨v| → |v⟩ (with appropriate basis)
    """
    return Ket(bra.label, Index(bra.index.name if bra.index else "i", "upper"))


def lower_index(ket: Ket, metric: Dict[str, Dict[str, Fraction]]) -> Bra:
    """
    Lower index using metric tensor gᵢⱼ.
    
    vᵢ = gᵢⱼ vʲ
    
    In bra-ket: |v⟩ → ⟨v| (with appropriate basis)
    """
    return Bra(ket.label, Index(ket.index.name if ket.index else "i", "lower"))


# ============================================================================
# Tensor Rank
# ============================================================================

def rank(term: Term) -> Tuple[int, int]:
    """
    Compute tensor rank: (contravariant, covariant).
    
    |v⟩ = (1, 0) - vector (one upper index)
    ⟨v| = (0, 1) - covector (one lower index)
    |v⟩⟨w| = (1, 1) - operator (one upper, one lower)
    ⟨v|w| = (0, 0) - scalar
    """
    atoms = flatten(term)
    upper = sum(1 for a in atoms if isinstance(a, Ket))
    lower = sum(1 for a in atoms if isinstance(a, Bra))
    return (upper, lower)


# ============================================================================
# Step-by-Step Visualization
# ============================================================================

def show_tensor_product():
    """Show tensor products."""
    print("\n" + "="*60)
    print("TENSOR PRODUCTS")
    print("="*60)
    
    # Two vectors
    a = Ket("a", Index("i", "upper"))
    b = Ket("b", Index("j", "upper"))
    
    print(f"\n|a⟩ ⊗ |b⟩ = {tensor(a, b)}")
    print(f"  Two contravariant vectors → rank (2, 0) tensor")
    print(f"  In index notation: aⁱ bʲ")
    
    # Vector and covector
    v = Ket("v", Index("i", "upper"))
    w = Bra("w", Index("j", "lower"))
    
    print(f"\n|v⟩ ⊗ ⟨w| = {tensor(v, w)}")
    print(f"  Vector ⊗ Covector → rank (1, 1) operator")
    print(f"  In index notation: vⁱ wⱼ")


def show_contraction():
    """Show contraction / yanking."""
    print("\n" + "="*60)
    print("CONTRACTION (YANKING)")
    print("="*60)
    
    print("\n  The yanking rule IS tensor contraction!")
    print("  ⟨x|x⟩ → ─")
    print("  Repeated index = sum (Einstein convention)")
    
    # Simple contraction
    v_bra = Bra("v", Index("i", "lower"))
    v_ket = Ket("v", Index("i", "upper"))
    
    product = tensor(v_bra, v_ket)
    contracted = contract(product)
    
    print(f"\n  ⟨vᵢ| ⊗ |vⁱ⟩ = {product}")
    print(f"  Contract: {contracted}")
    print(f"  (sum over i: vᵢ vⁱ = |v|²)")
    
    # Matrix-vector multiplication
    M = tensor(Ket("e", Index("i", "upper")), Bra("e", Index("j", "lower")))
    x = Ket("x", Index("j", "upper"))
    
    Mx = tensor(M, x)
    result = contract(Mx)
    
    print(f"\n  Matrix-vector: M|x⟩")
    print(f"  |eⁱ⟩⟨eⱼ| ⊗ |xʲ⟩ = {Mx}")
    print(f"  Contract over j: |eⁱ⟩⟨eⱼ|xʲ⟩ → {result}")
    print(f"  (sum over j: eⁱ eⱼ xʲ)")


def show_outer_inner():
    """Show outer and inner products."""
    print("\n" + "="*60)
    print("OUTER & INNER PRODUCTS")
    print("="*60)
    
    # Basis vectors
    e1 = Ket("e₁")
    e2 = Ket("e₂")
    
    # Outer product: |e₁⟩⟨e₂|
    outer = outer_product(e1, Bra("e₂"))
    print(f"\nOuter product: |e₁⟩⟨e₂| = {outer}")
    print(f"  Creates rank-2 operator/matrix")
    print(f"  Matrix element M₁₂ = 1, others = 0")
    
    # Inner product: ⟨e₁|e₁⟩
    inner = inner_product(Bra("e₁"), e1)
    print(f"\nInner product: ⟨e₁|e₁⟩ = {inner}")
    print(f"  Creates scalar (rank 0)")
    print(f"  = 1 (for orthonormal basis)")
    
    # Non-orthogonal: ⟨e₁|e₂⟩
    inner2 = inner_product(Bra("e₁"), e2)
    print(f"\nNon-orthogonal: ⟨e₁|e₂⟩ = {inner2}")
    print(f"  = 0 (for orthonormal basis)")


def show_adjoints():
    """Show adjoint operations."""
    print("\n" + "="*60)
    print("ADJOINTS & TRANSPOSE")
    print("="*60)
    
    v = Ket("v", Index("i", "upper"))
    print(f"\n|v⟩ = {v}")
    print(f"(|v⟩)† = {adjoint(v)}")
    
    op = tensor(Ket("a"), Bra("b"))
    print(f"\nOperator: |a⟩⟨b| = {op}")
    print(f"(|a⟩⟨b|)† = {adjoint(op)}")
    print(f"  (swap and reverse)")


def show_rank():
    """Show tensor rank."""
    print("\n" + "="*60)
    print("TENSOR RANK")
    print("="*60)
    
    examples = [
        (Ket("v"), "Vector (contravariant)"),
        (Bra("v"), "Covector (covariant)"),
        (tensor(Ket("v"), Bra("w")), "Operator/matrix"),
        (tensor(Ket("a"), Ket("b")), "Rank-2 contravariant"),
        (tensor(Bra("a"), Bra("b")), "Rank-2 covariant"),
        (tensor(tensor(Ket("a"), Ket("b")), Bra("c")), "Rank (2, 1)"),
    ]
    
    for term, desc in examples:
        r = rank(term)
        print(f"\n{term:30} rank {r}  {desc}")


def show_trace():
    """Show trace operations."""
    print("\n" + "="*60)
    print("TRACE")
    print("="*60)
    
    # Trace of |v⟩⟨v|
    v_ket = Ket("v", Index("i", "upper"))
    v_bra = Bra("v", Index("i", "lower"))
    
    op = tensor(v_ket, v_bra)
    print(f"\nTr(|v⟩⟨v|)")
    print(f"  |vⁱ⟩⟨vᵢ| = {op}")
    print(f"  Contract: {trace(op)}")
    print(f"  = |v|² (squared norm)")
    
    # Identity matrix
    e1 = Ket("e", Index("1", "upper"))
    e1_bra = Bra("e", Index("1", "lower"))
    e2 = Ket("e", Index("2", "upper"))
    e2_bra = Bra("e", Index("2", "lower"))
    
    I = tensor(tensor(e1, e1_bra), tensor(e2, e2_bra))
    print(f"\nIdentity matrix (2D):")
    print(f"  I = |e₁⟩⟨e₁| + |e₂⟩⟨e₂| = {I}")
    print(f"  Tr(I) = 2 (dimension)")


def show_einstein():
    """Show Einstein summation convention."""
    print("\n" + "="*60)
    print("EINSTEIN SUMMATION CONVENTION")
    print("="*60)
    
    print("\n  In tensor calculus:")
    print("    Repeated index (one up, one down) = sum")
    print()
    print("  aᵢ bⁱ = Σᵢ aᵢ bⁱ  (inner product)")
    print()
    print("  In bra-ket:")
    print("    ⟨a|b⟩ where |b⟩ = bⁱ|eᵢ⟩")
    print("    = Σᵢ ⟨a|eᵢ⟩⟨eᵢ|b⟩  (resolution of identity)")
    print()
    print("  The yanking rule ⟨x|x⟩ → ─ IS the summation!")
    print("  Contracting matching bra-ket pairs = summing over that index")


# ============================================================================
# Demo
# ============================================================================

def demo():
    print("="*60)
    print("SPINOR TENSOR CALCULUS")
    print("="*60)
    print()
    print("GRAMMAR: term ::= |x⟩ | ⟨x| | term ⊗ term")
    print("REWRITE: ⟨x|x⟩ → ─  (contraction/yanking)")
    print()
    print("This IS Dirac notation, which IS tensor calculus!")
    print()
    
    show_tensor_product()
    show_contraction()
    show_outer_inner()
    show_adjoints()
    show_rank()
    show_trace()
    show_einstein()
    
    print("\n" + "="*60)
    print("THE UNIFIED PICTURE")
    print("="*60)
    print()
    print("  Bra-ket notation ALREADY IS tensor calculus:")
    print()
    print("  ┌─────────────┬─────────────┬─────────────┐")
    print("  │ Concept     │ Dirac       │ Tensors     │")
    print("  ├─────────────┼─────────────┼─────────────┤")
    print("  │ Vector      │ |v⟩         │ vⁱ          │")
    print("  │ Covector    │ ⟨v|         │ vᵢ          │")
    print("  │ Inner prod  │ ⟨v|w⟩       │ vᵢ wⁱ      │")
    print("  │ Outer prod  │ |v⟩⟨w|      │ vⁱ wⱼ      │")
    print("  │ Identity    │ |eᵢ⟩⟨eᵢ|   │ δᵢʲ        │")
    print("  │ Contraction │ ⟨x|x⟩ → ─   │ aᵢ bⁱ     │")
    print("  │ Adjoint     │ †           │ transpose   │")
    print("  └─────────────┴─────────────┴─────────────┘")
    print()
    print("  ONE GRAMMAR, ONE RULE.")
    print("  Linear algebra = Tensor calculus = Quantum mechanics.")
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        demo()