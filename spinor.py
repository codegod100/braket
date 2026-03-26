#!/usr/bin/env python3
"""
Bra-Ket Grammar: Everything from Spinors

The minimal grammar:
    term ::= |x⟩    (ket)
           | ⟨x|    (bra)
           | term term   (juxtaposition)

    rewrite: |x⟩⟨x| → ε   (yank to wire/empty)

Everything emerges:
- Identity = ability to insert |x⟩⟨x| anywhere
- Cap = the introduction rule (nothing → |x⟩⟨x|)
- Cup = the elimination rule (|x⟩⟨x| → nothing)
- Tensor = side-by-side terms
- Compose = matching bra/ket in sequence
- Types = inferred from connectivity
"""

from dataclasses import dataclass
from typing import Union, Optional, Iterator, Tuple
import re


# ============================================================================
# Terms - The Grammar
# ============================================================================

@dataclass(frozen=True)
class Ket:
    """Ket: |x⟩"""
    label: str
    
    def __str__(self):
        return f"|{self.label}⟩"
    
    def __repr__(self):
        return f"Ket({self.label!r})"
    
    def __format__(self, fmt):
        return format(str(self), fmt)


@dataclass(frozen=True)
class Bra:
    """Bra: ⟨x|"""
    label: str
    
    def __str__(self):
        return f"⟨{self.label}|"
    
    def __repr__(self):
        return f"Bra({self.label!r})"
    
    def __format__(self, fmt):
        return format(str(self), fmt)


@dataclass(frozen=True)
class Juxt:
    """Juxtaposition: t₁ t₂ (tensor or compose)"""
    left: 'Term'
    right: 'Term'
    
    def __str__(self):
        return f"{self.left}{self.right}"
    
    def __repr__(self):
        return f"Juxt({self.left!r}, {self.right!r})"
    
    def __format__(self, fmt):
        return format(str(self), fmt)


@dataclass(frozen=True)
class Wire:
    """The empty term / identity wire"""
    def __str__(self):
        return "─"
    
    def __repr__(self):
        return "Wire()"
    
    def __format__(self, fmt):
        return format(str(self), fmt)


Term = Union[Wire, Ket, Bra, Juxt]


# ============================================================================
# Parsing
# ============================================================================

def parse(s: str) -> Term:
    """Parse bra-ket string into term.
    
    Supports:
    - |x⟩      : ket
    - ⟨x|      : bra  
    - ⟨x|y⟩    : inner product (shorthand for ⟨x||y⟩)
    - |x⟩⟨y|   : outer product
    - Multiple atoms in sequence
    """
    s = s.strip()
    
    if not s or s == '─':
        return Wire()
    
    # Parse into atoms
    atoms = []
    i = 0
    while i < len(s):
        if s[i] == '|':
            # Ket: |x⟩
            j = s.index('⟩', i)
            atoms.append(Ket(s[i+1:j]))
            i = j + 1
        elif s[i] == '⟨':
            # Bra: ⟨x| or inner product ⟨x|y⟩
            # Find the closing | of the bra
            j = s.index('|', i)
            atoms.append(Bra(s[i+1:j]))
            i = j + 1
            
            # Check if next char is ⟩ (empty) or a label + ⟩ (inner product shorthand)
            if i < len(s) and s[i] != '⟨' and s[i] != '|':
                # Inner product shorthand: ⟨x|y⟩
                # Parse y⟩ as a ket
                k = s.index('⟩', i)
                atoms.append(Ket(s[i:k]))
                i = k + 1
        elif s[i] == ' ':
            i += 1
        else:
            raise ValueError(f"Unexpected character: {s[i]}")
    
    # Build juxtaposition (left-associative)
    if not atoms:
        return Wire()
    
    result = atoms[0]
    for atom in atoms[1:]:
        result = Juxt(result, atom)
    
    return result


# ============================================================================
# The Yank: |x⟩⟨x| → ε
# ============================================================================

def yank_one(term: Term) -> Term:
    """
    Apply ONE yank rewrite: |x⟩⟨x| → Wire() or ⟨x||x⟩ → Wire()
    Returns the term unchanged if no yank applies.
    """
    if isinstance(term, Wire):
        return term
    
    if isinstance(term, (Ket, Bra)):
        return term
    
    if isinstance(term, Juxt):
        # Pattern 1: |x⟩⟨x| (ket followed by bra)
        if isinstance(term.left, Ket) and isinstance(term.right, Bra):
            if term.left.label == term.right.label:
                return Wire()
        
        # Pattern 2: ⟨x||x⟩ (bra followed by ket)  
        if isinstance(term.left, Bra) and isinstance(term.right, Ket):
            if term.left.label == term.right.label:
                return Wire()
        
        # Pattern 3: (left |x⟩) (⟨x| right) - split across nested structure
        # Check if rightmost of left matches leftmost of right
        left_atoms = atoms(term.left)
        right_atoms = atoms(term.right)
        
        if left_atoms and right_atoms:
            last = left_atoms[-1]
            first = right_atoms[0]
            
            # Check for ⟨x| followed by |x⟩ across the boundary
            if isinstance(last, Bra) and isinstance(first, Ket):
                if last.label == first.label:
                    # Yank these two, reconstruct remainder
                    new_left = remove_last_atom(term.left)
                    new_right = remove_first_atom(term.right)
                    return yank_one(juxt(new_left, new_right))
            
            # Check for |x⟩ followed by ⟨x| across the boundary
            if isinstance(last, Ket) and isinstance(first, Bra):
                if last.label == first.label:
                    new_left = remove_last_atom(term.left)
                    new_right = remove_first_atom(term.right)
                    return yank_one(juxt(new_left, new_right))
    
    return term


def remove_last_atom(term: Term) -> Term:
    """Remove the last atom from a term, returning Wire if empty."""
    if isinstance(term, (Ket, Bra)):
        return Wire()
    if isinstance(term, Juxt):
        new_right = remove_last_atom(term.right)
        if isinstance(new_right, Wire):
            return term.left
        return Juxt(term.left, new_right)
    return term


def remove_first_atom(term: Term) -> Term:
    """Remove the first atom from a term, returning Wire if empty."""
    if isinstance(term, (Ket, Bra)):
        return Wire()
    if isinstance(term, Juxt):
        new_left = remove_first_atom(term.left)
        if isinstance(new_left, Wire):
            return term.right
        return Juxt(new_left, term.right)
    return term


def juxt(left: Term, right: Term) -> Term:
    """Smart juxtaposition that handles Wire()."""
    if isinstance(left, Wire) and isinstance(right, Wire):
        return Wire()
    if isinstance(left, Wire):
        return right
    if isinstance(right, Wire):
        return left
    return Juxt(left, right)


def yank(term: Term) -> Term:
    """
    Apply the yanking rewrite: |x⟩⟨x| → Wire() or ⟨x||x⟩ → Wire()
    
    This is the ONLY rewrite rule. Everything else follows.
    """
    yanked = yank_one(term)
    if yanked == term:
        # No more single yanks possible, recurse into subterms
        if isinstance(term, Juxt):
            left_yanked = yank(term.left)
            right_yanked = yank(term.right)
            return juxt(left_yanked, right_yanked)
        return term
    return yanked


def normalize(term: Term, max_steps: int = 100) -> Term:
    """Repeatedly apply yanking until fixed point."""
    for _ in range(max_steps):
        yanked = yank(term)
        if yanked == term:
            return term
        term = yanked
    return term


# ============================================================================
# The Inverse: Introducing Identity
# ============================================================================

def introduce(term: Term, label: str) -> Term:
    """
    The inverse of yanking: insert |x⟩⟨x| anywhere.
    
    This is the "cap" - the ability to create from nothing.
    In quantum terms: create a particle-antiparticle pair.
    """
    identity = Juxt(Ket(label), Bra(label))
    
    if isinstance(term, Wire):
        return identity
    
    # Can insert on either side or between
    # Return multiple possibilities
    return [
        Juxt(identity, term),   # Insert left
        Juxt(term, identity),  # Insert right
    ]


# ============================================================================
# Structural Analysis
# ============================================================================

def atoms(term: Term) -> list[Union[Ket, Bra]]:
    """Flatten to atomic components."""
    if isinstance(term, Wire):
        return []
    if isinstance(term, (Ket, Bra)):
        return [term]
    if isinstance(term, Juxt):
        return atoms(term.left) + atoms(term.right)
    return []


def count_kets(term: Term) -> int:
    """Count ket atoms."""
    return sum(1 for a in atoms(term) if isinstance(a, Ket))


def count_bras(term: Term) -> int:
    """Count bra atoms."""
    return sum(1 for a in atoms(term) if isinstance(a, Bra))


def balance(term: Term) -> int:
    """
    Balance = #kets - #bras.
    
    Balance determines the "type":
    - balance > 0: "output" type (more kets = outputs)
    - balance < 0: "input" type (more bras = inputs)
    - balance = 0: "closed" type (scalar/operator)
    """
    return count_kets(term) - count_bras(term)


def is_closed(term: Term) -> bool:
    """A closed term has equal kets and bras."""
    return balance(term) == 0


# ============================================================================
# Emergent Structure
# ============================================================================

def as_scalar(term: Term) -> Union[int, str]:
    """
    If term is closed and yanks to wire, it's the identity scalar 1.
    If it yanks to nothing (0 atoms), it's 0.
    Otherwise it's a nontrivial scalar.
    """
    normalized = normalize(term)
    
    if isinstance(normalized, Wire):
        return 1
    
    remaining = atoms(normalized)
    if not remaining:
        return 1  # All yanked away = identity scalar
    
    return str(normalized)


def as_operator(term: Term) -> Tuple[list[str], list[str]]:
    """
    Extract input/output types from a term.
    
    Returns (inputs, outputs) where:
    - inputs = unmatched bra labels
    - outputs = unmatched ket labels
    """
    normalized = normalize(term)
    remaining = atoms(normalized)
    
    inputs = [a.label for a in remaining if isinstance(a, Bra)]
    outputs = [a.label for a in remaining if isinstance(a, Ket)]
    
    return (inputs, outputs)


# ============================================================================
# Visualization
# ============================================================================

def diagram(term: Term) -> str:
    """Render term as a wire diagram."""
    normalized = normalize(term)
    
    if isinstance(normalized, Wire):
        return "──────────"
    
    atoms_list = atoms(normalized)
    if not atoms_list:
        return "──────────"
    
    # Build diagram row by row
    lines = []
    
    # Top: connectors for kets
    ket_line = ""
    for a in atoms_list:
        if isinstance(a, Ket):
            ket_line += "  ●─"
        else:
            ket_line += "    "
    if ket_line.strip():
        lines.append(ket_line)
    
    # Middle: labels
    label_line = ""
    for a in atoms_list:
        label_line += f" {a.label} "
    lines.append(label_line)
    
    # Bottom: connectors for bras  
    bra_line = ""
    for a in atoms_list:
        if isinstance(a, Bra):
            bra_line += "  ─●"
        else:
            bra_line += "    "
    if bra_line.strip():
        lines.append(bra_line)
    
    return "\n".join(lines)


# ============================================================================
# Interactive Grammar
# ============================================================================

def explain_term(term: Term) -> str:
    """Explain what a term represents."""
    bal = balance(term)
    normalized = normalize(term)
    
    if isinstance(normalized, Wire):
        return "Identity (empty after yanking)"
    
    explanations = []
    
    if bal == 0:
        explanations.append("Closed (scalar or operator)")
        remaining = atoms(normalized)
        if len(remaining) == 0:
            explanations.append("All yanked away → scalar 1")
        elif len(remaining) == 2:
            if isinstance(remaining[0], Ket) and isinstance(remaining[1], Bra):
                if remaining[0].label != remaining[1].label:
                    explanations.append(f"Operator |{remaining[0].label}⟩⟨{remaining[1].label}|")
    elif bal > 0:
        explanations.append(f"Output type (balance +{bal})")
        explanations.append(f"  {bal} unpaired ket(s)")
    elif bal < 0:
        explanations.append(f"Input type (balance {bal})")
        explanations.append(f"  {-bal} unpaired bra(s)")
    
    return " | ".join(explanations)


# ============================================================================
# Demo
# ============================================================================

def demo():
    print("=" * 60)
    print("BRA-KET GRAMMAR: Everything from Spinors")
    print("=" * 60)
    print()
    print("The ONLY rule: |x⟩⟨x| → ─ (yank to wire)")
    print("Everything else emerges from this.")
    print()
    
    print("-" * 60)
    print("1. THE YANK - Identity Emerges")
    print("-" * 60)
    
    # |x⟩⟨x| yanks to wire
    t = parse("|x⟩⟨x|")
    print(f"\n  {t}  →  {normalize(t)}")
    print(f"  {explain_term(t)}")
    
    print()
    print("  This IS the identity! The cap/cup vanish into a wire.")
    
    print("\n" + "-" * 60)
    print("2. NON-MATCHING - Operator Remains")
    print("-" * 60)
    
    # |y⟩⟨x| doesn't yank (different labels)
    t = parse("|y⟩⟨x|")
    print(f"\n  {t}  →  {normalize(t)}")
    print(f"  {explain_term(t)}")
    print("  Different labels: can't yank, operator remains")
    
    print("\n" + "-" * 60)
    print("3. CLOSED SCALAR - Inner Product")
    print("-" * 60)
    
    # ⟨x|x⟩ is a scalar
    t = parse("⟨x||x⟩")
    print(f"\n  ⟨x|x⟩ = {t}  →  {normalize(t)}")
    print(f"  {explain_term(t)}")
    print("  Bra meets matching ket → yanks to identity scalar 1")
    
    # ⟨x|y⟩ for x≠y
    t = parse("⟨x||y⟩")
    print(f"\n  ⟨x|y⟩ = {t}  →  {normalize(t)}")
    print(f"  {explain_term(t)}")
    print("  Different labels: can't yank, scalar remains")
    
    print("\n" + "-" * 60)
    print("4. COMPOSITION - Sequential Application")
    print("-" * 60)
    
    # |z⟩⟨y|y⟩⟨x| - chain
    t = parse("|z⟩⟨y||y⟩⟨x|")
    print(f"\n  {t}")
    print(f"  → {normalize(t)}")
    print(f"  {explain_term(t)}")
    print("  Inner ⟨y||y⟩ yanks, leaving |z⟩⟨x|")
    
    print("\n" + "-" * 60)
    print("5. INTRODUCING IDENTITY - The Cap Emerges")
    print("-" * 60)
    
    print("""
  The yank goes one way: |x⟩⟨x| → ─
  
  But we can always INSERT |x⟩⟨x| anywhere!
  This is the "cap" - creating from nothing:
  
         │           │
         │    →      ●─○
         │           │ │
                     ○─●
                     │
  
  The ability to insert identity is the DUAL of yanking.
  Together they give us the full compact closed structure.
    """)
    
    print("-" * 60)
    print("6. THE GRAMMAR IN FULL")
    print("-" * 60)
    
    print("""
  TERMS:
    |x⟩     ket (spinor "up")
    ⟨x|     bra (spinor "down")  
    t₁ t₂   juxtaposition (parallel/sequential)

  REWRITE:
    |x⟩⟨x| → ─   (yank matching pair)

  EMERGENT:
    ─        = identity / wire
    |x⟩⟨x|   = cap (creation) = id = cup (annihilation)
    |y⟩⟨x|   = operator (x≠y)
    ⟨x|x⟩   = scalar 1
    ⟨x|y⟩   = scalar 0 (x≠y, in orthonormal basis)

  TYPES (from balance):
    balance > 0  →  output type (kets exceed bras)
    balance < 0  →  input type (bras exceed kets)
    balance = 0  →  closed (scalar or operator)
    """)
    
    print("=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    print()
    print("  There are ONLY spinors (bras and kets).")
    print("  Caps, cups, wires, types — all EMERGE from:")
    print()
    print("    1. The grammar: bra, ket, juxtaposition")
    print("    2. The yank: |x⟩⟨x| → ─")
    print()
    print("  This is the MINIMAL foundation for categorical QM.")
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--demo':
            demo()
        elif sys.argv[1] == '--repl':
            # Simple REPL
            print("Bra-Ket REPL. Type 'q' to quit.\n")
            while True:
                try:
                    s = input("⟩ ").strip()
                    if s == 'q':
                        break
                    if not s:
                        continue
                    t = parse(s)
                    n = normalize(t)
                    print(f"  → {n}")
                    print(f"  [{explain_term(t)}]")
                except Exception as e:
                    print(f"  Error: {e}")
        else:
            # Parse and show
            t = parse(sys.argv[1])
            print(f"Parsed:  {t}")
            print(f"Yanked:  {normalize(t)}")
            print(f"Balance: {balance(t)}")
            print(f"Info:    {explain_term(t)}")
    else:
        demo()