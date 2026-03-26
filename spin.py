#!/usr/bin/env python3
"""
Spinor Language: A tiny toy language where everything is spinors.

Syntax:
  |x⟩         ket
  ⟨x|         bra
  ⟨x|y⟩       inner product
  (t1 t2)     juxtaposition/application
  let n = t   definition
  eval t      compute

Computation:
  |x⟩⟨x| → ─   (yank to identity)

Values emerge:
  Numbers = count of ● pairs
  Functions = operators that transform
  Booleans = TRUE = |x⟩⟨x|, FALSE = |y⟩⟨x|
"""

from dataclasses import dataclass
from typing import Union, Dict, List, Optional, Tuple
import re
import sys


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
    def __str__(self):
        l = f"({self.left})" if isinstance(self.left, Juxt) else str(self.left)
        r = f"({self.right})" if isinstance(self.right, Juxt) else str(self.right)
        return f"{l} {r}"
    def __repr__(self): return f"Juxt({self.left!r}, {self.right!r})"


@dataclass(frozen=True)
class Wire:
    def __str__(self): return "─"
    def __repr__(self): return "Wire()"
    def __format__(self, fmt): return format(str(self), fmt)


@dataclass
class Var:
    """Named variable/reference"""
    name: str
    def __str__(self): return self.name
    def __repr__(self): return f"Var({self.name!r})"


@dataclass
class Let:
    """let name = value in body"""
    name: str
    value: 'Term'
    body: 'Term'
    def __str__(self): return f"(let {self.name} = {self.value} in {self.body})"


@dataclass
class Def:
    """Top-level definition"""
    name: str
    value: 'Term'
    def __str__(self): return f"let {self.name} = {self.value}"


@dataclass
class Eval:
    """Evaluate a term"""
    term: 'Term'
    def __str__(self): return f"eval {self.term}"


Term = Union[Wire, Ket, Bra, Juxt, Var, Let, Def, Eval]


# ============================================================================
# Parser
# ============================================================================

class Parser:
    """Parse spinor language."""
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.defs: Dict[str, Term] = {}
    
    def peek(self) -> Optional[str]:
        self.skip_whitespace()
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None
    
    def skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in ' \t\n':
            self.pos += 1
    
    def consume(self, expected: str):
        self.skip_whitespace()
        if self.source[self.pos:self.pos+len(expected)] != expected:
            raise ValueError(f"Expected '{expected}' at position {self.pos}")
        self.pos += len(expected)
    
    def parse_program(self) -> List[Union[Def, Eval]]:
        """Parse a program (multiple definitions and evals)."""
        statements = []
        while self.peek():
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        return statements
    
    def parse_statement(self) -> Optional[Union[Def, Eval]]:
        """Parse a top-level statement."""
        self.skip_whitespace()
        
        if self.peek() is None:
            return None
        
        # Look ahead for keywords
        start_pos = self.pos
        word = self.parse_word()
        
        if word == "let":
            name = self.parse_word()
            self.consume("=")
            value = self.parse_term()
            return Def(name, value)
        
        if word == "eval":
            term = self.parse_term()
            return Eval(term)
        
        # Not a keyword - backtrack and parse as term for eval
        self.pos = start_pos
        term = self.parse_term()
        return Eval(term)
    
    def parse_word(self) -> str:
        """Parse an identifier/keyword."""
        self.skip_whitespace()
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos].isalnum():
            self.pos += 1
        return self.source[start:self.pos]
    
    def parse_term(self) -> Term:
        """Parse a term - may be a sequence of juxtaposed atoms."""
        self.skip_whitespace()
        
        c = self.peek()
        
        if c is None:
            return Wire()
        
        terms = []
        
        # Keep parsing atoms until we hit a delimiter
        while True:
            c = self.peek()
            
            if c is None or c == '\n':
                break
            if c == ')':
                break
            if c == ';':  # Statement separator
                break
            
            if c == '|':
                terms.append(self.parse_ket())
            elif c == '⟨':
                terms.append(self.parse_bra_or_inner())
            elif c == '(':
                terms.append(self.parse_parens())
            elif c == '─':
                self.pos += 1
                terms.append(Wire())
            elif c == '_':
                self.pos += 1
                terms.append(Wire())
            elif c.isalpha():
                name = self.parse_word()
                terms.append(Var(name))
            elif c.isdigit():
                n = self.parse_number()
                terms.append(self.num_to_unary(n))
            else:
                break
            
            self.skip_whitespace()
        
        if not terms:
            return Wire()
        
        # Build left-associative juxtaposition
        result = terms[0]
        for t in terms[1:]:
            result = Juxt(result, t)
        return result
    
    def parse_ket(self) -> Ket:
        """Parse |x⟩"""
        self.consume("|")
        label = self.parse_label()
        self.consume("⟩")
        return Ket(label)
    
    def parse_bra_or_inner(self) -> Term:
        """Parse ⟨x| or ⟨x|y⟩"""
        self.consume("⟨")
        label1 = self.parse_label()
        self.consume("|")
        
        # Check if this is an inner product ⟨x|y⟩
        # Only if the next char is a valid label character (not ⟩, ), space, etc.)
        c = self.peek()
        if c and c not in '⟩⟨|()\n\t ':
            label2 = self.parse_label()
            self.consume("⟩")
            # Inner product is bra + ket
            return Juxt(Bra(label1), Ket(label2))
        
        # Just a bra
        return Bra(label1)
    
    def parse_label(self) -> str:
        """Parse a label (identifier or symbol)."""
        self.skip_whitespace()
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos] not in '⟩|⟨ \t\n()':
            self.pos += 1
        return self.source[start:self.pos]
    
    def parse_parens(self) -> Term:
        """Parse (term) or (term term ...) - multiple juxtaposed terms."""
        self.consume("(")
        
        terms = [self.parse_term()]
        
        # Collect all terms until closing paren
        while True:
            self.skip_whitespace()
            if self.peek() == ')':
                break
            terms.append(self.parse_term())
        
        self.consume(")")
        
        # Build left-associative juxtaposition
        result = terms[0]
        for t in terms[1:]:
            result = Juxt(result, t)
        return result
    
    def parse_number(self) -> int:
        """Parse a number."""
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self.pos += 1
        return int(self.source[start:self.pos])
    
    def num_to_unary(self, n: int) -> Term:
        """Convert number n to unary spinor representation.
        
        Use CHAINED pairs that don't self-yank:
        n = |#0⟩⟨#1⟩ |#1⟩⟨#2⟩ ... |#{n-1}⟩⟨#{n}⟩
        
        This is a "wire" from #0 to #n with n segments.
        Each segment is a pair that WON'T self-yank (different labels).
        The count of pairs = the number n.
        """
        if n == 0:
            return Wire()
        
        units = []
        for i in range(n):
            # Chain: from i to i+1
            unit = Juxt(Ket(f"#{i}"), Bra(f"#{i+1}"))
            units.append(unit)
        
        result = units[0]
        for u in units[1:]:
            result = Juxt(result, u)
        return result


def parse(source: str) -> List[Union[Def, Eval]]:
    """Parse source code into statements."""
    return Parser(source).parse_program()


# ============================================================================
# Yanking (Computation)
# ============================================================================

def atoms(t: Term) -> List[Union[Ket, Bra]]:
    """Flatten to atomic components."""
    if isinstance(t, Wire): return []
    if isinstance(t, (Ket, Bra)): return [t]
    if isinstance(t, Juxt): return atoms(t.left) + atoms(t.right)
    if isinstance(t, Var): return [t]  # Keep vars
    return []


def yank_one(t: Term) -> Term:
    """Apply one yank step: |x⟩⟨x| → ─"""
    if isinstance(t, (Wire, Ket, Bra, Var)):
        return t
    
    if isinstance(t, Juxt):
        # Direct patterns
        if isinstance(t.left, Ket) and isinstance(t.right, Bra):
            if t.left.label == t.right.label:
                return Wire()
        if isinstance(t.left, Bra) and isinstance(t.right, Ket):
            if t.left.label == t.right.label:
                return Wire()
        
        # Nested yank
        left_y = yank_one(t.left)
        if left_y != t.left:
            return juxt(left_y, t.right)
        right_y = yank_one(t.right)
        if right_y != t.right:
            return juxt(t.left, right_y)
        
        # Cross-boundary yank
        atoms_l = atoms(t.left)
        atoms_r = atoms(t.right)
        
        if atoms_l and atoms_r:
            last, first = atoms_l[-1], atoms_r[0]
            
            # Only yank matching Ket-Bra or Bra-Ket, not Vars
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
    if isinstance(t, (Ket, Bra, Var)): return Wire()
    if isinstance(t, Juxt):
        r = remove_last(t.right)
        return t.left if isinstance(r, Wire) else Juxt(t.left, r)
    return t


def remove_first(t: Term) -> Term:
    if isinstance(t, (Ket, Bra, Var)): return Wire()
    if isinstance(t, Juxt):
        l = remove_first(t.left)
        return t.right if isinstance(l, Wire) else Juxt(l, t.right)
    return t


def normalize(t: Term, steps: int = 100) -> Term:
    """Fully normalize a term by repeated yanking."""
    for _ in range(steps):
        yanked = yank_one(t)
        if yanked == t:
            return t
        t = yanked
    return t


# ============================================================================
# Built-in Values
# ============================================================================

def make_true() -> Term:
    """TRUE = |x⟩⟨x| (identity, matches everything)"""
    return Juxt(Ket("x"), Bra("x"))


def make_false() -> Term:
    """FALSE = |y⟩⟨x| (constant, never matches)"""
    return Juxt(Ket("y"), Bra("x"))


def make_succ() -> Term:
    """SUCC as a function that appends a unit.
    
    This is tricky because we need to generate fresh labels.
    For now, represent SUCC as a placeholder that will be
    handled specially during interpretation.
    """
    return Var("__succ__")  # Special form handled by interpreter


def make_zero() -> Term:
    """ZERO = ─ (empty wire)"""
    return Wire()


def make_identity() -> Term:
    """ID = |x⟩⟨x|"""
    return Juxt(Ket("x"), Bra("x"))


def make_compose() -> Term:
    """COMPOSE = λf.λg. f ∘ g (represented structurally)"""
    return Var("compose")  # Placeholder


def make_add() -> Term:
    """ADD for numbers - special form handled by interpreter."""
    return Var("__add__")


def add_numbers(a: Term, b: Term) -> Term:
    """Add two numbers by composing their chains.
    
    If a = |#0⟩⟨#n⟩ and b = |#0⟩⟨#m⟩,
    then a + b = |#0⟩⟨#{n+m}⟩
    
    We reindex b to start where a ends, then compose.
    """
    na = count_unary(a)
    nb = count_unary(b)
    
    if na == 0:
        return b
    if nb == 0:
        return a
    
    # Result is |#0⟩⟨#{na+nb}⟩
    return Juxt(Ket("#0"), Bra(f"#{na+nb}"))


# ============================================================================
# Interpretation
# ============================================================================

def count_unary(t: Term) -> int:
    """Count unary representation.
    
    Numbers are chains that yank to endpoint form:
    n = |#0⟩⟨#n⟩ after normalization
    
    Count by reading the endpoint distance.
    """
    a = atoms(t)
    
    # First, check if it's an endpoint form |#0⟩⟨#n⟩
    if len(a) == 2:
        if isinstance(a[0], Ket) and isinstance(a[1], Bra):
            if a[0].label.startswith("#") and a[1].label.startswith("#"):
                try:
                    start = int(a[0].label[1:])
                    end = int(a[1].label[1:])
                    return end - start
                except ValueError:
                    pass
    
    # Otherwise, count the pairs directly
    count = 0
    i = 0
    while i < len(a) - 1:
        if isinstance(a[i], Ket) and isinstance(a[i+1], Bra):
            if a[i].label.startswith("#") and a[i+1].label.startswith("#"):
                count += 1
                i += 2
                continue
        i += 1
    return count


def fresh_index(t: Term) -> int:
    """Find the next fresh index for a number's # labels."""
    a = atoms(t)
    max_idx = -1
    for atom in a:
        if isinstance(atom, (Ket, Bra)) and atom.label.startswith("#"):
            try:
                idx = int(atom.label[1:])  # Get number after #
                max_idx = max(max_idx, idx)
            except ValueError:
                pass
    return max_idx + 1


def succ_number(t: Term) -> Term:
    """Successor: append a new segment to the chain.
    
    If n = |#0⟩⟨#1⟩ ... |#{n-1}⟩⟨#{n}⟩
    Then n+1 = |#0⟩⟨#1⟩ ... |#{n}⟩⟨#{n+1}⟩
    """
    next_idx = fresh_index(t)
    if isinstance(t, Wire):
        # 0 → 1: |#0⟩⟨#1|
        return Juxt(Ket("#0"), Bra("#1"))
    
    # Find the last segment and extend
    # Actually, just append |#{next_idx-1}⟩⟨#{next_idx}|
    # Wait, we need to connect: the last segment ends at #{n}
    # We need to add |#{n}⟩⟨#{n+1}|
    # But fresh_index gives n+1, so we need n
    
    # Find what the last index is (the current endpoint)
    last_idx = next_idx - 1  # This is n, where n = count_unary(t)
    # But fresh_index returns max+1, and we want to extend from last to last+1
    # Actually, if the chain goes #0→#1→...→#n, then fresh_index returns n+1
    # And we need to add |#n⟩⟨#n+1⟩
    
    # Simpler: count current segments, then extend
    n = count_unary(t)
    new_unit = Juxt(Ket(f"#{n}"), Bra(f"#{n+1}"))
    return juxt(t, new_unit)


def interpret_term(t: Term, env: Dict[str, Term] = None) -> Term:
    """Interpret a term in an environment."""
    if env is None:
        env = {}
    
    if isinstance(t, Var):
        if t.name == "__succ__":
            return Var("__succ__")  # Keep as special form
        if t.name in env:
            return env[t.name]
        if t.name in BUILTINS:
            return BUILTINS[t.name]
        return t  # Unbound var
    
    if isinstance(t, Juxt):
        l = interpret_term(t.left, env)
        r = interpret_term(t.right, env)
        
        # Special handling for SUCC
        if isinstance(l, Var) and l.name == "__succ__":
            return succ_number(r)
        
        # Special handling for ADD
        if isinstance(l, Var) and l.name == "__add__":
            return add_numbers(Wire(), r)  # ADD x = 0 + x
        
        # Check if both are numbers - then this is addition!
        la = atoms(l)
        lr = atoms(r)
        
        is_num_l = (len(la) == 2 and 
                   isinstance(la[0], Ket) and isinstance(la[1], Bra) and
                   la[0].label.startswith("#") and la[1].label.startswith("#"))
        is_num_r = (len(lr) == 2 and 
                   isinstance(lr[0], Ket) and isinstance(lr[1], Bra) and
                   lr[0].label.startswith("#") and lr[1].label.startswith("#"))
        
        if is_num_l and is_num_r:
            return add_numbers(l, r)
        
        return normalize(juxt(l, r))
    
    if isinstance(t, Let):
        new_env = {**env, t.name: interpret_term(t.value, env)}
        return interpret_term(t.body, new_env)
    
    return t


BUILTINS = {
    "TRUE": make_true(),
    "FALSE": make_false(),
    "SUCC": make_succ(),
    "ADD": make_add(),
    "ZERO": make_zero(),
    "ID": make_identity(),
    "ONE": Juxt(Ket("#0"), Bra("#1")),
    "TWO": Juxt(Juxt(Ket("#0"), Bra("#1")), Juxt(Ket("#1"), Bra("#2"))),
    "THREE": Juxt(Juxt(Juxt(Ket("#0"), Bra("#1")), Juxt(Ket("#1"), Bra("#2"))), Juxt(Ket("#2"), Bra("#3"))),
}


def run_program(source: str) -> List[Tuple[str, Term]]:
    """Run a program and return results."""
    statements = parse(source)
    env = dict(BUILTINS)
    results = []
    
    for stmt in statements:
        if isinstance(stmt, Def):
            env[stmt.name] = interpret_term(stmt.value, env)
            results.append(("def", stmt.name))
        elif isinstance(stmt, Eval):
            val = interpret_term(stmt.term, env)
            results.append(("eval", val))
    
    return results


# ============================================================================
# REPL
# ============================================================================

def repl():
    """Interactive read-eval-print loop."""
    print("Spinor Language REPL")
    print("Type 'quit' to exit, 'help' for commands\n")
    
    env = dict(BUILTINS)
    
    while True:
        try:
            line = input("⟩ ").strip()
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue
        
        if not line:
            continue
        
        if line == "quit":
            break
        
        if line == "help":
            print("""
Commands:
  quit          Exit REPL
  help          Show this help
  env           Show environment
  clear         Clear environment

Syntax:
  |x⟩           Ket
  ⟨x|           Bra
  ⟨x|y⟩         Inner product
  (t1 t2)       Juxtaposition
  let n = t     Definition
  eval t        Evaluate
  0, 1, 2...    Numbers (auto-convert to unary)

Builtins:
  TRUE, FALSE, ID, SUCC, ZERO, ONE, TWO, THREE

Examples:
  eval |x⟩⟨x|
  eval ⟨x|x⟩
  let two = 2
  eval (SUCC two)
  eval ⟨a|b⟩
""")
            continue
        
        if line == "env":
            for name, val in env.items():
                print(f"  {name} = {val}")
            print()
            continue
        
        if line == "clear":
            env = dict(BUILTINS)
            print("Environment cleared.\n")
            continue
        
        # Parse and evaluate
        try:
            statements = parse(line)
            for stmt in statements:
                if isinstance(stmt, Def):
                    env[stmt.name] = interpret_term(stmt.value, env)
                    print(f"  {stmt.name} defined")
                elif isinstance(stmt, Eval):
                    val = interpret_term(stmt.term, env)
                    print(f"  {val}")
                    # Show interpretation
                    n = count_unary(val)
                    if n > 0:
                        print(f"  = {n} (unary)")
        except Exception as e:
            print(f"  Error: {e}")
        
        print()


# ============================================================================
# Demo
# ============================================================================

def demo():
    """Demonstrate the spinor language."""
    print("=" * 60)
    print("SPINOR LANGUAGE: A tiny toy language")
    print("=" * 60)
    print()
    
    examples = [
        # Basic yanking
        ("eval |x⟩⟨x|", "Identity yanks to wire"),
        ("eval ⟨x|x⟩", "Inner product yanks to wire"),
        ("eval ⟨x|y⟩", "Non-matching doesn't yank"),
        
        # Numbers
        ("eval 0", "Zero is empty wire"),
        ("eval 3", "3 = chain |#0⟩⟨#3⟩ (endpoint form)"),
        ("eval (SUCC 2)", "Successor: 2+1=3"),
        ("eval (SUCC (SUCC 1))", "Double successor: 1+1+1=3"),
        
        # Arithmetic
        ("let a = 2", "Define a = 2"),
        ("let b = 3", "Define b = 3"),
        ("eval (a b)", "Addition: 2+3=5"),
        
        # Functions
        ("eval ID", "Identity function"),
        ("eval (ID |x⟩)", "Apply identity"),
        ("eval TRUE", "True = identity"),
        ("eval FALSE", "False = constant"),
        
        # Composition
        ("eval (|y⟩⟨x| |x⟩⟨x|)", "Function application"),
        ("eval (|z⟩⟨y| (|y⟩⟨x| |x⟩⟨x|))", "Chain: z←y←x"),
    ]
    
    env = dict(BUILTINS)
    
    for code, comment in examples:
        print(f"  {code}")
        print(f"  # {comment}")
        
        try:
            statements = parse(code)
            for stmt in statements:
                if isinstance(stmt, Def):
                    env[stmt.name] = interpret_term(stmt.value, env)
                    print(f"  → {stmt.name} defined")
                elif isinstance(stmt, Eval):
                    val = interpret_term(stmt.term, env)
                    print(f"  → {val}")
                    n = count_unary(val)
                    if n > 0 and isinstance(val, Juxt):
                        print(f"  → {n} (unary)")
        except Exception as e:
            print(f"  Error: {e}")
        
        print()
    
    print("=" * 60)
    print("The language has:")
    print("  - 2 term constructors: ket |x⟩, bra ⟨x|")
    print("  - 1 combinator: juxtaposition (t1 t2)")
    print("  - 1 rewrite rule: |x⟩⟨x| → ─")
    print("  - Everything else emerges!")
    print("=" * 60)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--demo":
            demo()
        elif arg == "--repl":
            repl()
        elif arg.endswith(".spin"):
            # Run file
            with open(arg) as f:
                source = f.read()
            for typ, val in run_program(source):
                if typ == "def":
                    print(f"{val} defined")
                else:
                    print(f"→ {val}")
                    n = count_unary(val)
                    if n > 0:
                        print(f"  = {n}")
        else:
            # Evaluate argument
            for typ, val in run_program(arg):
                print(f"→ {val}")
    else:
        repl()