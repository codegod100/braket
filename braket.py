#!/usr/bin/env python3
"""
Bra-Ket to Lambda Calculus Converter

Maps quantum Dirac notation to lambda calculus expressions.

Key mappings:
- |x⟩⟨x| → λx.x (identity/projection)
- |y⟩⟨x| → λx.y (constant function)
- |x⟩ → variable x (ket as term)
- ⟨x| → abstraction context (bra as binder)

The outer product |φ⟩⟨ψ| acts as a function: applying to |χ⟩ yields ⟨ψ|χ⟩|φ⟩
"""

from dataclasses import dataclass
from typing import Union
import re


# ============================================================================
# Lambda Calculus AST
# ============================================================================

@dataclass
class Var:
    """Variable in lambda calculus"""
    name: str
    
    def __str__(self):
        return self.name
    
    def __eq__(self, other):
        return isinstance(other, Var) and self.name == other.name
    
    def __hash__(self):
        return hash(('Var', self.name))


@dataclass
class Lam:
    """Lambda abstraction: λx.body"""
    param: str
    body: 'Term'
    
    def __str__(self):
        return f"λ{self.param}.{self.body}"
    
    def __eq__(self, other):
        return isinstance(other, Lam) and self.param == other.param and self.body == other.body
    
    def __hash__(self):
        return hash(('Lam', self.param, self.body))


@dataclass
class App:
    """Application: f x"""
    func: 'Term'
    arg: 'Term'
    
    def __str__(self):
        func_str = f"({self.func})" if isinstance(self.func, Lam) else str(self.func)
        arg_str = f"({self.arg})" if isinstance(self.arg, (Lam, App)) else str(self.arg)
        return f"{func_str} {arg_str}"
    
    def __eq__(self, other):
        return isinstance(other, App) and self.func == other.func and self.arg == other.arg
    
    def __hash__(self):
        return hash(('App', self.func, self.arg))


Term = Union[Var, Lam, App]


# ============================================================================
# Bra-Ket AST
# ============================================================================

@dataclass
class Ket:
    """Ket: |x⟩"""
    label: str
    
    def __str__(self):
        return f"|{self.label}⟩"
    
    def __repr__(self):
        return f"Ket({self.label!r})"


@dataclass
class Bra:
    """Bra: ⟨x|"""
    label: str
    
    def __str__(self):
        return f"⟨{self.label}|"
    
    def __repr__(self):
        return f"Bra({self.label!r})"


@dataclass
class BraKet:
    """Inner product: ⟨x|y⟩"""
    bra_label: str
    ket_label: str
    
    def __str__(self):
        return f"⟨{self.bra_label}|{self.ket_label}⟩"
    
    def __repr__(self):
        return f"BraKet({self.bra_label!r}, {self.ket_label!r})"
    
    def evaluate(self) -> Union[int, str]:
        """Evaluate inner product (Kronecker delta for basis states)"""
        if self.bra_label == self.ket_label:
            return 1  # ⟨x|x⟩ = 1
        else:
            return 0  # ⟨x|y⟩ = 0 for x ≠ y


@dataclass
class OuterProduct:
    """Outer product: |y⟩⟨x|"""
    ket_label: str  # result
    bra_label: str  # input/binder
    
    def __str__(self):
        return f"|{self.ket_label}⟩⟨{self.bra_label}|"
    
    def __repr__(self):
        return f"OuterProduct({self.ket_label!r}, {self.bra_label!r})"


@dataclass 
class OpApp:
    """Operator application: Op |x⟩"""
    operator: Union[OuterProduct, 'CompositeOp']
    ket: Ket
    
    def __str__(self):
        return f"{self.operator}{self.ket}"


@dataclass
class CompositeOp:
    """Composite operator: Op1 Op2"""
    left: Union[OuterProduct, 'CompositeOp']
    right: Union[OuterProduct, 'CompositeOp']
    
    def __str__(self):
        return f"{self.left}{self.right}"


BraKetTerm = Union[Ket, Bra, BraKet, OuterProduct, OpApp, CompositeOp]


# ============================================================================
# Parsers
# ============================================================================

def parse_lambda(s: str) -> Term:
    """Parse lambda calculus expression.
    
    Supports:
    - Variables: x, y, z
    - Abstractions: λx.x, λx.λy.x
    - Applications: (f x), f x, f g x (left-associative)
    """
    s = s.strip()
    
    # Abstraction: λx.body or \x.body
    if s.startswith(('λ', '\\')):
        # Find the dot
        dot_idx = s.index('.')
        param = s[1:dot_idx].strip()
        body_str = s[dot_idx+1:].strip()
        body = parse_lambda(body_str)
        return Lam(param, body)
    
    # Application (left-associative): f x y = ((f x) y)
    # Check if there's a space-separated application
    if ' ' in s and not s.startswith('('):
        parts = split_application(s)
        if len(parts) > 1:
            result = parse_lambda(parts[0])
            for part in parts[1:]:
                result = App(result, parse_lambda(part))
            return result
    
    # Parenthesized expression
    if s.startswith('(') and s.endswith(')'):
        return parse_lambda(s[1:-1])
    
    # Variable
    return Var(s)


def split_application(s: str) -> list[str]:
    """Split application into parts, respecting parentheses."""
    parts = []
    current = ""
    depth = 0
    
    for c in s:
        if c == '(':
            depth += 1
            current += c
        elif c == ')':
            depth -= 1
            current += c
        elif c == ' ' and depth == 0:
            if current:
                parts.append(current)
                current = ""
        else:
            current += c
    
    if current:
        parts.append(current)
    
    return parts


def parse_braket(s: str) -> BraKetTerm:
    """Parse bra-ket notation.
    
    Supports:
    - Ket: |x⟩
    - Bra: ⟨x|
    - Inner product: ⟨x|y⟩
    - Outer product: |y⟩⟨x|
    - Operator application: |y⟩⟨x||z⟩
    """
    s = s.strip()
    
    # Try to match different patterns
    
    # Operator application: outer product applied to ket
    # Pattern: |y⟩⟨x||z⟩  or  |y⟩⟨x| |z⟩
    app_match = re.match(r'^\|([^⟩]+)⟩⟨([^|]+)\|\|?([^⟩]+)⟩$', s)
    if app_match:
        ket_label, bra_label, input_ket = app_match.groups()
        return OpApp(OuterProduct(ket_label, bra_label), Ket(input_ket))
    
    # Outer product: |y⟩⟨x|
    outer_match = re.match(r'^\|([^⟩]+)⟩⟨([^|]+)\|$', s)
    if outer_match:
        ket_label, bra_label = outer_match.groups()
        return OuterProduct(ket_label, bra_label)
    
    # Inner product: ⟨x|y⟩
    inner_match = re.match(r'^⟨([^|]+)\|([^⟩]+)⟩$', s)
    if inner_match:
        bra_label, ket_label = inner_match.groups()
        return BraKet(bra_label, ket_label)
    
    # Ket: |x⟩
    ket_match = re.match(r'^\|([^⟩]+)⟩$', s)
    if ket_match:
        return Ket(ket_match.group(1))
    
    # Bra: ⟨x|
    bra_match = re.match(r'^⟨([^|]+)\|$', s)
    if bra_match:
        return Bra(bra_match.group(1))
    
    raise ValueError(f"Cannot parse bra-ket expression: {s}")


# ============================================================================
# Converters
# ============================================================================

def braket_to_lambda(term: BraKetTerm) -> Term:
    """Convert bra-ket notation to lambda calculus.
    
    The key insight:
    - |y⟩⟨x| is a function/operator that binds x and returns y
    - |x⟩⟨x| ≈ λx.x (identity on x)
    - |y⟩⟨x| ≈ λx.y (constant function returning y)
    - |x⟩ ≈ x (the term itself)
    """
    
    if isinstance(term, Ket):
        # |x⟩ → x (just the variable)
        return Var(term.label)
    
    elif isinstance(term, Bra):
        # ⟨x| → context/abstraction marker
        # This doesn't have a direct lambda equivalent alone
        return Var(f"⟨{term.label}|")
    
    elif isinstance(term, BraKet):
        # ⟨x|y⟩ → evaluates to 0 or 1 (Kronecker delta)
        # In lambda calculus: λx.λy.(x y) with Church encoding
        # For simplicity, we return a Church-encoded boolean
        if term.bra_label == term.ket_label:
            return Var("1")  # Church: λt.λf.t
        else:
            return Var("0")  # Church: λt.λf.f
    
    elif isinstance(term, OuterProduct):
        # |y⟩⟨x| → λx.y
        # The bra ⟨x| binds x, the ket |y⟩ is what's returned
        return Lam(term.bra_label, Var(term.ket_label))
    
    elif isinstance(term, OpApp):
        # (|y⟩⟨x|) |z⟩ → (λx.y) z
        func = braket_to_lambda(term.operator)
        arg = Var(term.ket.label)
        return App(func, arg)
    
    elif isinstance(term, CompositeOp):
        # Composition of operators
        # For now, just chain them
        raise NotImplementedError("Composite operators not yet supported")
    
    raise ValueError(f"Unknown term type: {type(term)}")


def lambda_to_braket(term: Term) -> BraKetTerm:
    """Convert lambda calculus to bra-ket notation.
    
    Reverse mapping:
    - λx.x → |x⟩⟨x| (identity/projector)
    - λx.y → |y⟩⟨x| (constant function)
    - x → |x⟩ (variable as ket)
    """
    
    if isinstance(term, Var):
        # x → |x⟩
        return Ket(term.name)
    
    elif isinstance(term, Lam):
        # Check the body
        if isinstance(term.body, Var):
            if term.body.name == term.param:
                # λx.x → |x⟩⟨x| (identity)
                return OuterProduct(term.param, term.param)
            else:
                # λx.y → |y⟩⟨x| (constant)
                return OuterProduct(term.body.name, term.param)
        else:
            # Complex body - try to convert recursively
            body_braket = lambda_to_braket(term.body)
            # This is more complex - we'd need proper type tracking
            raise NotImplementedError(f"Complex lambda body not yet supported: {term}")
    
    elif isinstance(term, App):
        # f x → apply operator to ket
        func_braket = lambda_to_braket(term.func)
        arg_braket = lambda_to_braket(term.arg)
        
        if isinstance(func_braket, OuterProduct) and isinstance(arg_braket, Ket):
            return OpApp(func_braket, arg_braket)
        
        raise NotImplementedError(f"Application conversion not yet supported: {term}")
    
    raise ValueError(f"Unknown term type: {type(term)}")


# ============================================================================
# Beta Reduction
# ============================================================================

def free_vars(term: Term) -> set[str]:
    """Get free variables in a term."""
    if isinstance(term, Var):
        return {term.name}
    elif isinstance(term, Lam):
        return free_vars(term.body) - {term.param}
    elif isinstance(term, App):
        return free_vars(term.func) | free_vars(term.arg)
    return set()


def substitute(term: Term, var: str, replacement: Term) -> Term:
    """Substitute a variable with a term."""
    if isinstance(term, Var):
        if term.name == var:
            return replacement
        return term
    elif isinstance(term, Lam):
        if term.param == var:
            return term  # var is bound
        if term.param in free_vars(replacement):
            # Need alpha conversion
            new_param = term.param + "'"
            new_body = substitute(term.body, term.param, Var(new_param))
            return Lam(new_param, substitute(new_body, var, replacement))
        return Lam(term.param, substitute(term.body, var, replacement))
    elif isinstance(term, App):
        return App(substitute(term.func, var, replacement),
                   substitute(term.arg, var, replacement))
    return term


def beta_reduce(term: Term) -> Term:
    """Perform beta reduction."""
    if isinstance(term, Var):
        return term
    elif isinstance(term, Lam):
        return Lam(term.param, beta_reduce(term.body))
    elif isinstance(term, App):
        if isinstance(term.func, Lam):
            # (λx.body) arg → body[x := arg]
            return substitute(term.func.body, term.func.param, beta_reduce(term.arg))
        else:
            # Reduce subterms
            reduced_func = beta_reduce(term.func)
            if reduced_func != term.func:
                return beta_reduce(App(reduced_func, term.arg))
            reduced_arg = beta_reduce(term.arg)
            if reduced_arg != term.arg:
                return beta_reduce(App(term.func, reduced_arg))
            return App(term.func, term.arg)
    return term


def normalize(term: Term, max_steps: int = 100) -> Term:
    """Normalize a term by repeated beta reduction."""
    for _ in range(max_steps):
        reduced = beta_reduce(term)
        if reduced == term:
            return term
        term = reduced
    return term


# ============================================================================
# Bra-Ket Evaluation
# ============================================================================

def evaluate_braket(term: BraKetTerm) -> Union[BraKetTerm, int]:
    """Evaluate bra-ket expressions."""
    
    if isinstance(term, BraKet):
        return term.evaluate()
    
    elif isinstance(term, OpApp):
        # (|y⟩⟨x|) |z⟩
        if isinstance(term.operator, OuterProduct):
            # Compute inner product ⟨x|z⟩
            inner = BraKet(term.operator.bra_label, term.ket.label)
            scalar = inner.evaluate()
            
            if scalar == 0:
                return 0  # Orthogonal states
            else:
                # Return the ket scaled by the inner product
                if scalar == 1:
                    return Ket(term.operator.ket_label)
                else:
                    return f"{scalar}·|{term.operator.ket_label}⟩"
    
    elif isinstance(term, OuterProduct):
        return term  # Already in normal form
    
    elif isinstance(term, Ket):
        return term
    
    return term


# ============================================================================
# Pretty Printing
# ============================================================================

def pretty_comparison(name: str, braket: str, lamb: str, result: str = None):
    """Print a nice comparison."""
    print(f"\n{name}:")
    print(f"  Bra-ket:  {braket}")
    print(f"  Lambda:   {lamb}")
    if result:
        print(f"  Result:   {result}")


def box_print(s: str, width: int = 50):
    """Print a boxed message."""
    print("\n" + "┌" + "─" * (width - 2) + "┐")
    for line in s.split('\n'):
        print(f"│ {line:<{width-4}} │")
    print("└" + "─" * (width - 2) + "┘")


# ============================================================================
# Interactive CLI
# ============================================================================

def interactive_mode():
    """Run interactive conversion mode."""
    box_print("Bra-Ket ↔ Lambda Calculus Converter\n\nType 'q' to quit, 'h' for help")
    
    while True:
        try:
            print("\n" + "─" * 50)
            user_input = input("⟩ ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'q':
                print("\nGoodbye!")
                break
            
            if user_input.lower() == 'h':
                show_help()
                continue
            
            if user_input.lower() == 'demo':
                run_demo()
                continue
            
            # Try to detect which notation
            if '|' in user_input or '⟩' in user_input or '⟨' in user_input:
                # Bra-ket notation
                term = parse_braket(user_input)
                lambda_term = braket_to_lambda(term)
                print(f"\n  → {lambda_term}")
                
                # Try to evaluate
                result = evaluate_braket(term)
                if result != term:
                    if isinstance(result, int):
                        print(f"  → {result}")
                    else:
                        print(f"  → {result}")
                
                # Show beta reduction if applicable
                if isinstance(lambda_term, App):
                    reduced = normalize(lambda_term)
                    if reduced != lambda_term:
                        print(f"  → {reduced} (reduced)")
            
            elif 'λ' in user_input or '\\' in user_input:
                # Lambda notation
                term = parse_lambda(user_input)
                braket_term = lambda_to_braket(term)
                print(f"\n  → {braket_term}")
            
            else:
                print("  Could not detect notation. Use |x⟩ for kets or λ for lambda.")
        
        except Exception as e:
            print(f"  Error: {e}")


def show_help():
    """Show help message."""
    print("""
Commands:
  q       - Quit
  h       - Show this help
  demo    - Run demonstration

Bra-ket examples:
  |x⟩         → x
  |x⟩⟨x|      → λx.x
  |y⟩⟨x|      → λx.y
  |y⟩⟨x||z⟩   → (λx.y) z → y (if x=z) or 0 (if x≠z)
  ⟨x|y⟩       → 1 (if x=y) or 0 (if x≠y)

Lambda examples:
  λx.x        → |x⟩⟨x|
  λx.y        → |y⟩⟨x|
  (λx.y) z    → |y⟩⟨x||z⟩
""")


def run_demo():
    """Run demonstration of key mappings."""
    box_print("DEMONSTRATION: Bra-Ket ↔ Lambda Calculus")
    
    print("\n" + "=" * 50)
    print("CORE MAPPINGS")
    print("=" * 50)
    
    # 1. Identity
    print("\n1. IDENTITY / PROJECTOR")
    bk = parse_braket("|x⟩⟨x|")
    lm = braket_to_lambda(bk)
    pretty_comparison("Identity", str(bk), str(lm))
    print("  Meaning: Projects onto state |x⟩, or returns x unchanged")
    
    # 2. Constant function
    print("\n2. CONSTANT FUNCTION")
    bk = parse_braket("|y⟩⟨x|")
    lm = braket_to_lambda(bk)
    pretty_comparison("Constant", str(bk), str(lm))
    print("  Meaning: Ignores input, always returns y")
    
    # 3. Application - matching
    print("\n3. APPLICATION (matching state)")
    bk = parse_braket("|y⟩⟨x||x⟩")
    lm = braket_to_lambda(bk)
    result = evaluate_braket(bk)
    reduced = normalize(lm)
    pretty_comparison("Apply to matching", str(bk), str(lm), f"{result}")
    print(f"  Reduced: {reduced}")
    print("  Meaning: ⟨x|x⟩=1, so result is |y⟩")
    
    # 4. Application - orthogonal
    print("\n4. APPLICATION (orthogonal state)")
    bk = parse_braket("|y⟩⟨x||z⟩")
    lm = braket_to_lambda(bk)
    result = evaluate_braket(bk)
    reduced = normalize(lm)
    pretty_comparison("Apply to orthogonal", str(bk), str(lm), f"{result}")
    print(f"  Reduced: {reduced} (no reduction, x≠z)")
    print("  Meaning: ⟨x|z⟩=0, so result is 0")
    
    # 5. Inner product
    print("\n5. INNER PRODUCT")
    bk = parse_braket("⟨x|x⟩")
    result = evaluate_braket(bk)
    pretty_comparison("Self inner product", str(bk), "δ_{xx}", str(result))
    
    bk = parse_braket("⟨x|y⟩")
    result = evaluate_braket(bk)
    pretty_comparison("Orthogonal inner product", str(bk), "δ_{xy}", str(result))
    
    # Reverse mappings
    print("\n" + "=" * 50)
    print("REVERSE MAPPINGS (Lambda → Bra-ket)")
    print("=" * 50)
    
    print("\n6. LAMBDA IDENTITY → PROJECTOR")
    lm = parse_lambda("λx.x")
    bk = lambda_to_braket(lm)
    pretty_comparison("Identity function", str(lm), str(bk))
    
    print("\n7. LAMBDA CONSTANT → OPERATOR")
    lm = parse_lambda("λx.y")
    bk = lambda_to_braket(lm)
    pretty_comparison("Constant function", str(lm), str(bk))
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print("""
The correspondence is:
  
  Bra-ket              Lambda
  
  |x⟩                  x           (variable/term)
  ⟨x|                  binder      (abstraction context)
  |y⟩⟨x|               λx.y        (outer product = function)
  |x⟩⟨x|               λx.x        (projector = identity)
  ⟨x|y⟩                δ_{xy}      (inner product = Kronecker delta)
  |y⟩⟨x||z⟩            (λx.y) z    (operator application)

The outer product |y⟩⟨x| captures the essence of a function:
  - The bra ⟨x| binds the input variable
  - The ket |y⟩ specifies the output
  - Application is the inner product evaluation
""")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ['-h', '--help']:
            show_help()
        elif arg == '--demo':
            run_demo()
        else:
            # Convert the argument
            try:
                if '|' in arg or '⟩' in arg or '⟨' in arg:
                    term = parse_braket(arg)
                    print(f"Lambda: {braket_to_lambda(term)}")
                    result = evaluate_braket(term)
                    if result != term:
                        print(f"Result: {result}")
                else:
                    term = parse_lambda(arg)
                    print(f"Bra-ket: {lambda_to_braket(term)}")
            except Exception as e:
                print(f"Error: {e}")
    else:
        interactive_mode()