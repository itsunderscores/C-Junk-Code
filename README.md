## Junk Code Generator – C++ Console App

This project includes a Python script that generates C++ "junk" functions to add noise/obfuscation to a console application.

The generator creates a chain of functions; each performs meaningless work and then calls the next one. You trigger the whole chain with a single call to `JunkRun()`.

---

## 1. Files and Outputs

- **Generator script**: `junk_code_generator.py`
- **Reference (driver-style) generator**: `ref_junk_code_generator.py`

Running `junk_code_generator.py` produces two headers:

- `junk_functions.hpp`
  - Declares:
    - `volatile int entropy_vault = 0;`
    - `volatile const char* string_garbage_disposal = 0;`
    - `void JunkRun(void);`
    - All junk function prototypes (`void internal_module_...();`)
- `junk_functions2.hpp`
  - Includes `junk_functions.hpp`
  - Defines `void JunkRun(void)` which calls the first junk function in the chain
  - Contains all function implementations

---

## 2. Generating the junk headers

From the project root (same folder as `junk_code_generator.py`), run:

```bash
python junk_code_generator.py
```

This will generate 500 junk functions with the default settings in the current directory.

Common options:

- **Number of functions**

  ```bash
  python junk_code_generator.py --functions 300
  ```

- **Approximate statements per function**

  ```bash
  python junk_code_generator.py --statements 10
  ```

- **Fixed entry function name (optional)**

  ```bash
  python junk_code_generator.py --first-name internal_module_MyStart123
  ```

  If omitted, a random `internal_module_*` name is chosen automatically.

- **Custom output directory**

  ```bash
  python junk_code_generator.py --output-dir path/to/generated
  ```

- **Deterministic output (fixed seed)**

  ```bash
  python junk_code_generator.py --seed 1337
  ```

By default, the headers are written to the current directory:

- `./junk_functions.hpp`
- `./junk_functions2.hpp`

---

## 3. Integrating into your C++ console project

Assume you have a typical console `main.cpp` in a C++ project.

### 3.1. Add the generated headers to your project

1. Run `junk_code_generator.py` (see above).
2. Copy or move `junk_functions.hpp` and `junk_functions2.hpp` into a directory that your compiler can see, for example:
   - Same folder as `main.cpp`, or
   - A `include/` or `src/` folder that is already on the include path.

If you use a subfolder (e.g. `junk/`), adjust the include paths accordingly, e.g. `#include "junk/junk_functions.hpp"`.

### 3.2. Include order in `main.cpp`

In your console application, you call the junk chain once at startup.

**Simplest approach (same folder as `main.cpp`):**

```cpp
#include "junk_functions.hpp"
#include "junk_functions2.hpp"

int main() {
    // Run the junk chain once at startup
    JunkRun();

    // Your real program logic here
    // ...
}
```

If the headers are in a subfolder, use:

```cpp
#include "junk/junk_functions.hpp"
#include "junk/junk_functions2.hpp"
```

> Note: `junk_functions2.hpp` already includes `"junk_functions.hpp"` internally, but explicitly including `junk_functions.hpp` in `main.cpp` keeps the intent clear and avoids order issues if you later split things into multiple translation units.

---

## 4. Regenerating junk code

Whenever you want new junk:

1. Re-run `junk_code_generator.py` with your desired options.
2. Replace the old `junk_functions.hpp` and `junk_functions2.hpp` in your C++ project with the newly generated files.
3. Rebuild your project.

You **do not** need to change your C++ code as long as you keep calling:

```cpp
JunkRun();
```

The script will always wire `JunkRun()` to the first function in the newly generated chain.

---

## 5. Quick checklist

- [ ] Run `python junk_code_generator.py` (with options you want).
- [ ] Copy `junk_functions.hpp` and `junk_functions2.hpp` into your C++ project.
- [ ] Ensure your compiler’s include path can see these headers.
- [ ] In `main.cpp`:
  - [ ] `#include "junk_functions.hpp"`
  - [ ] `#include "junk_functions2.hpp"`
  - [ ] Call `JunkRun();` once at startup.
- [ ] Rebuild and run your console application.

