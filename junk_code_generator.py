#!/usr/bin/env python3
"""
Junk code generator for a C++ console application.

Generates:
  - junk_functions.hpp  (globals + JunkRun + prototypes)
  - junk_functions2.hpp (implementations)

The functions form a junk chain: each does meaningless work then calls the next.

Usage:
  python junk_code_generator.py [--functions N] [--statements M] [--first-name NAME] [--output-dir DIR]

In main.cpp (console app):
  #include "junk_functions.hpp"
  #include "junk_functions2.hpp"
  int main() {
      JunkRun();  // runs the entire junk chain
      // ...
  }
"""

import random
import string
import argparse
from pathlib import Path


SYMBOL_CHARS = "!@#$%^&*()-_+=[]{}|;:,.<>?~`"


def c_escape(s: str) -> str:
    """Escape for use inside a C/C++ double-quoted string literal."""
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
    )


def random_length_range(
    rng: random.Random,
    min_lo: int = 1,
    min_hi: int = 12,
    max_hi: int = 45,
) -> tuple[int, int]:
    """Random (min_len, max_len) so string length varies each time."""
    min_len = rng.randint(min_lo, min_hi)
    max_len = rng.randint(min_len, max(min_len, max_hi))
    return (min_len, max_len)


def random_id(
    prefix: str,
    length: int = 8,
    rng: random.Random | None = None,
) -> str:
    """Generate a random identifier: prefix + mixed alphanumeric."""
    r = rng or random
    chars = string.ascii_letters + string.digits
    return prefix + "".join(r.choices(chars, k=length))


def random_module_name(rng: random.Random) -> str:
    """Generate internal_module_<MixedCase> style name."""
    length = rng.randint(10, 14)
    first = rng.choice(string.ascii_letters)
    rest = "".join(
        rng.choices(string.ascii_letters + string.digits, k=length - 1)
    )
    return "internal_module_" + first + rest


def random_string_literal(
    rng: random.Random,
    min_len: int | None = None,
    max_len: int | None = None,
) -> str:
    """Alphanumeric, optionally with symbols. Length from random range if min/max not given."""
    if min_len is None or max_len is None:
        min_len, max_len = random_length_range(rng)
    use_symbols = rng.random() < 0.45
    chars = (
        string.ascii_letters + string.digits + SYMBOL_CHARS
        if use_symbols
        else string.ascii_letters + string.digits
    )
    n = rng.randint(min_len, max_len)
    return "".join(rng.choices(chars, k=n))


def random_string_noise(
    rng: random.Random,
    min_len: int | None = None,
    max_len: int | None = None,
) -> str:
    """String with newlines, tabs, spaces - will be C-escaped when written."""
    if min_len is None or max_len is None:
        min_len, max_len = random_length_range(rng, 2, 8, 40)
    fragments = [
        "\n",
        "\n\n",
        "\n\n\n",
        "\t",
        "\t\t",
        " ",
        "  ",
        "   ",
        " \n",
        "\n ",
        "\t\n",
        "\n\t",
        " \t ",
        " \n\t\n ",
        "\r\n",
        "\n\r",
    ]
    n = rng.randint(min_len, max_len)
    return "".join(rng.choices(fragments, k=n))


def random_string_mixed(
    rng: random.Random,
    min_len: int | None = None,
    max_len: int | None = None,
) -> str:
    """Mix of alphanumeric and symbols; occasional space, rarely \\n/\\t."""
    if min_len is None or max_len is None:
        min_len, max_len = random_length_range(rng)
    use_symbols = rng.random() < 0.5
    chars = (
        string.ascii_letters + string.digits + SYMBOL_CHARS
        if use_symbols
        else string.ascii_letters + string.digits
    )
    parts: list[str] = []
    for _ in range(rng.randint(2, 7)):
        if rng.random() < 0.12:
            parts.append(
                rng.choice(
                    [" ", "  ", "   "]
                    if rng.random() < 0.7
                    else ["\n", "\t"]
                )
            )
        else:
            parts.append(
                "".join(
                    rng.choices(
                        chars,
                        k=rng.randint(1, 8),
                    )
                )
            )
    candidate = "".join(parts)
    if len(candidate) < min_len:
        candidate += "".join(
            rng.choices(chars, k=min_len - len(candidate))
        )
    if len(candidate) > max_len:
        candidate = candidate[:max_len]
    return candidate


def _stmt_string_assign(
    rng: random.Random,
    lit_fn,
    *args,
    **kwargs,
) -> str:
    raw = lit_fn(rng, *args, **kwargs)
    return (
        '    string_garbage_disposal = (volatile const char*)"' + c_escape(raw) + '";'
    )


def generate_tiny(
    func_name: str,
    next_func_name: str | None,
    rng: random.Random,
) -> str:
    """Very small: 1–3 ints, 1–3 string assigns, few total statements."""
    n_ints = rng.randint(1, 3)
    int_vars = [f"iv_{random_id('', 4, rng)}_{i}" for i in range(n_ints)]
    int_vals = [rng.randint(-0x7FFFFFFF, 0x7FFFFFFF) for _ in range(n_ints)]
    lines: list[str] = [f"void {func_name}() {{"]
    for v, val in zip(int_vars, int_vals):
        lines.append(f"    int {v} = {val};")
    for _ in range(rng.randint(1, 3)):
        lines.append(
            _stmt_string_assign(
                rng,
                rng.choice([random_string_literal, random_string_mixed]),
            )
        )
    for _ in range(rng.randint(1, 3)):
        if int_vars:
            v = rng.choice(int_vars)
            if rng.random() < 0.5:
                lines.append(f"    entropy_vault += {v};")
            else:
                lines.append(f"    {v} += {rng.randint(-99, 99)};")
    if next_func_name:
        lines.append(f"    {next_func_name}();")
    lines.append("}")
    return "\n".join(lines)


def generate_int_only(
    func_name: str,
    next_func_name: str | None,
    rng: random.Random,
    statements: int,
) -> str:
    """No strings: just int locals and arithmetic."""
    n = rng.randint(3, 8)
    int_vars = [f"iv_{random_id('', 4, rng)}_{i}" for i in range(n)]
    int_vals = [rng.randint(-0x7FFFFFFF, 0x7FFFFFFF) for _ in range(n)]
    lines: list[str] = [f"void {func_name}() {{"]
    for v, val in zip(int_vars, int_vals):
        lines.append(f"    int {v} = {val};")
    for _ in range(statements):
        if len(int_vars) >= 2:
            a, b = rng.sample(int_vars, 2)
            op = rng.choice(["+", "-", "&", "|", "^"])
            if rng.random() < 0.6:
                lines.append(f"    {a} = {a} {op} {b};")
            else:
                lines.append(f"    entropy_vault += {a};")
    if next_func_name:
        lines.append(f"    {next_func_name}();")
    lines.append("}")
    return "\n".join(lines)


def generate_string_heavy(
    func_name: str,
    next_func_name: str | None,
    rng: random.Random,
) -> str:
    """Lots of string assigns: mostly alnum/symbols and mixed, rarely noise."""
    n_ints = rng.randint(2, 5)
    int_vars = [f"iv_{random_id('', 4, rng)}_{i}" for i in range(n_ints)]
    int_vals = [rng.randint(-0x7FFFFFFF, 0x7FFFFFFF) for _ in range(n_ints)]
    lines: list[str] = [f"void {func_name}() {{"]
    for v, val in zip(int_vars, int_vals):
        lines.append(f"    int {v} = {val};")
    for _ in range(rng.randint(8, 16)):
        kind = rng.choice(
            ["alnum", "alnum", "alnum", "mixed", "mixed", "noise"]
        )
        if kind == "noise":
            lines.append(_stmt_string_assign(rng, random_string_noise))
        elif kind == "mixed":
            lines.append(_stmt_string_assign(rng, random_string_mixed))
        else:
            lines.append(_stmt_string_assign(rng, random_string_literal))
    for _ in range(rng.randint(2, 5)):
        if int_vars:
            v = rng.choice(int_vars)
            lines.append(f"    entropy_vault += {v};")
    if next_func_name:
        lines.append(f"    {next_func_name}();")
    lines.append("}")
    return "\n".join(lines)


def generate_literal_heavy(
    func_name: str,
    next_func_name: str | None,
    rng: random.Random,
) -> str:
    """Many string assigns: only alnum/symbol literals, no \\n / \\t."""
    lines: list[str] = [f"void {func_name}() {{"]
    for _ in range(rng.randint(6, 14)):
        lines.append(
            _stmt_string_assign(
                rng,
                rng.choice([random_string_literal, random_string_mixed]),
            )
        )
    if next_func_name:
        lines.append(f"    {next_func_name}();")
    lines.append("}")
    return "\n".join(lines)


def generate_mixed(
    func_name: str,
    next_func_name: str | None,
    statements_per_func: int,
    rng: random.Random,
) -> str:
    """Int locals + mix of string literal styles + arithmetic."""
    num_ints = rng.randint(5, 11)
    int_vars = [f"iv_{random_id('', 4, rng)}_{i}" for i in range(num_ints)]
    int_values = [
        rng.randint(-0x7FFFFFFF, 0x7FFFFFFF) for _ in range(num_ints)
    ]
    lines: list[str] = [f"void {func_name}() {{"]

    for v, val in zip(int_vars, int_values):
        lines.append(f"    int {v} = {val};")
    for _ in range(rng.randint(3, 7)):
        kind = rng.choice(["alnum", "alnum", "mixed", "noise"])
        if kind == "noise":
            lines.append(_stmt_string_assign(rng, random_string_noise))
        elif kind == "mixed":
            lines.append(_stmt_string_assign(rng, random_string_mixed))
        else:
            lit = random_string_literal(rng)
            lines.append(
                '    string_garbage_disposal = (volatile const char*)"'
                + c_escape(lit)
                + '";'
            )

    for _ in range(statements_per_func):
        choice = rng.randint(0, 7)
        if choice == 0 and len(int_vars) >= 2:
            a, b = rng.sample(int_vars, 2)
            op = rng.choice(["| 1", "& -2", "^ 0"])
            lines.append(f"    {a} += ({b} {op});")
        elif choice == 1 and len(int_vars) >= 2:
            a, b = rng.sample(int_vars, 2)
            lines.append(f"    {a} -= ({b} ^ {rng.randint(0, 0xFFFF)});")
        elif choice == 2:
            lines.append(_stmt_string_assign(rng, random_string_literal))
        elif choice == 3:
            lines.append(_stmt_string_assign(rng, random_string_mixed))
        elif choice == 4 and len(int_vars) >= 2:
            a, b = rng.sample(int_vars, 2)
            lines.append(f"    {a} = {a} + {b};")
        elif choice == 5 and int_vars:
            v = rng.choice(int_vars)
            lines.append(f"    entropy_vault += {v};")
        elif choice == 6:
            lit = random_string_literal(rng)
            lines.append(
                '    string_garbage_disposal = (volatile const char*)"'
                + c_escape(lit)
                + '";'
            )
        else:
            if int_vars:
                v = rng.choice(int_vars)
                delta = rng.randint(-1000, 1000)
                lines.append(f"    {v} += {delta};")

    if next_func_name:
        lines.append(f"    {next_func_name}();")
    lines.append("}")
    return "\n".join(lines)


def generate_implementation(
    func_name: str,
    next_func_name: str | None,
    statements_per_func: int,
    rng: random.Random,
) -> str:
    """Pick a random style and generate one junk function."""
    styles = [
        ("tiny", lambda: generate_tiny(func_name, next_func_name, rng)),
        (
            "int_only",
            lambda: generate_int_only(
                func_name, next_func_name, rng, statements_per_func
            ),
        ),
        (
            "string_heavy",
            lambda: generate_string_heavy(func_name, next_func_name, rng),
        ),
        (
            "literal_heavy",
            lambda: generate_literal_heavy(func_name, next_func_name, rng),
        ),
        (
            "mixed",
            lambda: generate_mixed(
                func_name, next_func_name, statements_per_func, rng
            ),
        ),
    ]
    _, gen = rng.choice(styles)
    return gen()


def main():
    ap = argparse.ArgumentParser(
        description="Generate junk code headers for a C++ console application."
    )
    ap.add_argument(
        "--functions",
        "-n",
        type=int,
        default=500,
        help="Number of junk functions (default: 500)",
    )
    ap.add_argument(
        "--statements",
        "-s",
        type=int,
        default=12,
        help="Approximate statements per function (default: 12)",
    )
    ap.add_argument(
        "--first-name",
        default=None,
        help="Name of the first function (called from main). If omitted, a new random internal_module_* name is generated.",
    )
    ap.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("."),
        help="Output directory for .hpp files",
    )
    ap.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    args = ap.parse_args()
    rng = random.Random(args.seed)

    # Build names list: all new random internal_module_* names (or use --first-name to fix entry point)
    first_name = (
        args.first_name
        if args.first_name is not None
        else random_module_name(rng)
    )
    names = [first_name] + [
        random_module_name(rng) for _ in range(args.functions - 1)
    ]

    # Prototypes header (globals + JunkRun entrypoint + all prototypes)
    prototypes_lines = [
        "#pragma once",
        "",
        "volatile int entropy_vault = 0;",
        "volatile const char* string_garbage_disposal = 0;",
        "",
        "void JunkRun(void);  /* call this once at startup */",
        "",
        "// --- Function Prototypes ---",
    ]
    for n in names:
        prototypes_lines.append(f"void {n}();")
    prototypes_content = "\n".join(prototypes_lines)

    # Implementations: include prototypes, define JunkRun(), chain each function to the next
    impl_parts = [
        "#pragma once",
        "",
        '#include "junk_functions.hpp"',
        "",
        "void JunkRun(void) {",
        f"    {names[0]}();",
        "}",
        "",
    ]
    for i, name in enumerate(names):
        next_name = names[i + 1] if i + 1 < len(names) else None
        impl_parts.append(
            generate_implementation(name, next_name, args.statements, rng)
        )
    implementations_content = "\n".join(impl_parts)

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "junk_functions.hpp").write_text(prototypes_content.rstrip() + "\n", encoding="utf-8")
    (out_dir / "junk_functions2.hpp").write_text(implementations_content.rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {out_dir / 'junk_functions.hpp'} ({args.functions} prototypes)")
    print(f"Wrote {out_dir / 'junk_functions2.hpp'} ({args.functions} functions)")
    print("")
    print("In main.cpp (console): include junk_functions.hpp, call JunkRun(); once at startup, then include junk_functions2.hpp.")


if __name__ == "__main__":
    main()
