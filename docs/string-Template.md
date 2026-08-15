# `string.Template` usage — How-to Manual

Python's `string.Template` is a wonderfully boring choice for your use case: **standard library, stable, deliberately small, and enough structure to turn your current ad-hoc substitutions into a consistent convention.**

The important mental model is:

> A `Template` is a string containing named substitution fields.  
> A call to `.substitute()` or `.safe_substitute()` produces the instantiated string.

---

## 1. The basic pattern

```python
from string import Template

template = Template("""
APP_NAME = "$app_name"
IMPORT_NAME = "$import_name"
""")

result = template.substitute(
    app_name="cellshift",
    import_name="cellshift",
)
```

Result:

```python
APP_NAME = "cellshift"
IMPORT_NAME = "cellshift"
```

The `$name` syntax is the key difference from ordinary Python strings.

---

## 2. Keep templates separate from Python when they're substantial

For your `maxson-build-utils` structure, this is probably the sweet spot:

```text
templates/
    context.py
    cli.py
    gui.py
    changelog.md
    flatpak/
        manifest
        desktop
```

Then:

```python
from pathlib import Path
from string import Template

template_path = Path("templates/context.py")

template = Template(template_path.read_text())

result = template.substitute(
    app_name=pyproject.app_name,
    import_name=pyproject.import_name,
)
```

That keeps **content** in the template and **behavior** in the scaffold module.

---

# 3. Prefer named substitutions over positional formatting

Instead of:

```python
"{} {}".format(app_name, import_name)
```

use:

```python
Template("$app_name uses $import_name").substitute(
    app_name=app_name,
    import_name=import_name,
)
```

For scaffolding, names are much easier to maintain.

A template can have twenty fields without becoming a mystery about which positional argument corresponds to which value.

---

# 4. `$identifier` vs `${identifier}`

Both are supported.

### Simple form

```python
Template("$name.py")
```

### Braced form

```python
Template("${name}_config.py")
```

Use braces whenever the boundary isn't obvious.

For example:

```python
Template("${app_name}_errors.log")
```

rather than:

```python
Template("$app_name_errors.log")
```

The latter means the variable is named `app_name_errors`.

---

# 5. Literal dollar signs

Use `$$` for a literal `$`.

```python
Template("Price: $$100")
```

produces:

```text
Price: $100
```

This becomes particularly useful if one of your generated files itself contains shell variables:

```python
Template("""
#!/bin/sh
echo "Installing $$HOME/.local/bin"
""")
```

The generated file receives:

```sh
echo "Installing $HOME/.local/bin"
```

That's an easy one to forget.

---

# 6. `.substitute()` is your normal/default operation

This:

```python
template.substitute(
    app_name="cellshift",
    import_name="cellshift",
)
```

is intentionally strict.

If the template contains:

```text
$app_name
$import_name
$description
```

but you forget `description`, you get an error rather than silently producing a broken scaffold.

**For scaffolding, I strongly prefer this behavior.**

A missing value should generally be a failure.

---

# 7. `.safe_substitute()` exists — use it deliberately

```python
template.safe_substitute(
    app_name="cellshift",
)
```

will leave an unresolved variable rather than raising:

```text
cellshift
$description
```

This can be useful for partial/template composition, but I would **not make it your default scaffolding behavior**.

For project generation:

```python
.substitute()
```

is generally the safer choice.

You want:

> "You forgot to supply a value."

not:

> "Congratulations, you generated a file containing `$description`."

---

# 8. You can pass a dictionary

```python
values = {
    "app_name": "cellshift",
    "import_name": "cellshift",
    "pretty_name": "CellShift",
}

result = template.substitute(values)
```

This is particularly convenient if your scaffold already has metadata gathered into a mapping.

But don't feel compelled to convert your whole application model into dictionaries just because `Template` accepts mappings.

This is perfectly fine:

```python
template.substitute(
    app_name=pyproject.app_name,
    import_name=pyproject.import_name,
)
```

---

# 9. You can mix mapping and keyword arguments

Python permits:

```python
template.substitute(
    values,
    extra_value="something",
)
```

This can be handy for layered context.

For example:

```python
project_values = {
    "app_name": pyproject.app_name,
    "import_name": pyproject.import_name,
}

template.substitute(
    project_values,
    year="2026",
)
```

I'd use this sparingly, though. A single obvious source of template values is easier to reason about.

---

# 10. Read templates from files cleanly

For your project, I'd probably establish one little convention:

```python
from pathlib import Path
from string import Template


def read_template(path: Path) -> Template:
    return Template(path.read_text())
```

Then:

```python
template = read_template(
    Path("templates/context.py")
)

text = template.substitute(
    app_name=pyproject.app_name,
    import_name=pyproject.import_name,
)
```

The actual file reading and template instantiation become boring infrastructure.

---

# 11. Specify encoding explicitly for project templates

For a modern project, I like:

```python
path.read_text(encoding="utf-8")
```

and:

```python
path.write_text(text, encoding="utf-8")
```

That makes the filesystem contract explicit rather than depending on the platform's default encoding.

So a simple helper can be:

```python
def load_template(path: Path) -> Template:
    return Template(
        path.read_text(encoding="utf-8")
    )
```

---

# 12. Templates can contain arbitrary Python source

This is an important point for your scaffolder.

Nothing about `Template` cares whether the generated text is:

```text
Markdown
```

or:

```text
Python
```

or:

```text
TOML
```

or:

```text
Flatpak metadata
```

For example:

```python
Template("""
from pathlib import Path

APP_NAME = "$app_name"
APP_DIR = Path.home() / ".$app_name"
""")
```

is perfectly ordinary.

---

# 13. Keep logic OUT of the template

This is one of the biggest advantages of using `string.Template`.

Don't try to turn it into Jinja.

Don't invent:

```text
{% if gui %}
...
{% endif %}
```

Instead:

```python
if project.gui:
    render_template("gui.py", ...)
```

The template describes **text**.

Python describes **logic**.

That's a very healthy boundary for a scaffolding system.

---

# 14. Conditional sections belong in Python

Suppose Flatpak has one optional value.

Don't make the template responsible for determining whether the value exists.

Instead:

```python
if project.supports_web:
    template = load_template("flatpak-web-manifest")
else:
    template = load_template("flatpak-manifest")
```

or choose the appropriate values before rendering.

This keeps your templates extremely stupid—which is good.

---

# 15. Precompute derived values

This is a particularly nice pattern for your `PyProject`.

Don't make templates perform transformations.

Instead:

```python
values = {
    "app_name": pyproject.app_name,
    "pretty_name": pyproject.pretty_name,
    "import_name": pyproject.import_name,
    "service_name": pyproject.app_name,
}
```

Then:

```python
template.substitute(values)
```

If a value requires logic:

```python
service_name = make_service_name(pyproject.app_name)
```

do that **before** rendering.

The template receives the final answer.

---

# 16. `Template` objects are reusable

This is useful if you're generating multiple related files.

```python
template = Template(
    """
    Name=$app_name
    Version=$version
    """
)

for version in versions:
    template.substitute(
        app_name="cellshift",
        version=version,
    )
```

The template isn't consumed by rendering.

You can instantiate it repeatedly.

---

# 17. A very useful pattern: template factory

If you eventually have a templates directory, a small function is enough:

```python
from pathlib import Path
from string import Template

TEMPLATE_DIR = Path(__file__).parent / "templates"


def template(name: str) -> Template:
    path = TEMPLATE_DIR / name
    return Template(path.read_text(encoding="utf-8"))
```

Then:

```python
context_template = template("context.py")

text = context_template.substitute(
    app_name=pyproject.app_name,
    import_name=pyproject.import_name,
)
```

This is the kind of tiny abstraction I'd favor over adopting a framework.

---

# 18. Use `Template`'s validation when appropriate

`Template` exposes:

```python
template.is_valid()
```

and:

```python
template.get_identifiers()
```

These are useful for testing templates.

For example:

```python
assert template.is_valid()
```

and:

```python
assert template.get_identifiers() == {
    "app_name",
    "import_name",
}
```

That opens up a nice possibility for your test suite:

```text
tests/
    test_templates.py
```

where your templates can be checked without actually scaffolding an entire application.

---

# 19. `get_identifiers()` is particularly interesting for your ecosystem

Imagine:

```python
template = load_template("context.py")

print(template.get_identifiers())
```

and getting:

```python
{
    "app_name",
    "pretty_name",
    "import_name",
    "description",
}
```

Now the scaffold has an explicit dependency on the project's metadata.

That can be useful for tests and diagnostics.

For example, you could test that every identifier expected by a template is available from your scaffold context.

---

# 20. Subclassing `Template` is possible — but don't rush into it

`string.Template` is a class and can be subclassed.

It has class attributes controlling the template syntax, including the delimiter.

So technically you can create:

```python
class MaxsonTemplate(Template):
    ...
```

But I would **not do this initially**.

One of the beauties of your choice is that you're using the standard syntax:

```text
$app_name
${import_name}
```

Don't turn that into:

```text
@{app_name}
```

just because you can.

Boring is good.

---

# 21. Custom delimiters are available

If you ever need one:

```python
class MyTemplate(Template):
    delimiter = "%"
```

But again:

**don't.**

Not unless you encounter a real collision with `$` in the generated content.

Standard syntax makes your templates recognizable to any Python developer.

---

# 22. A particularly good convention: one template, one output artifact

For scaffolding, I'd favor:

```text
templates/
    context.py
    cli.py
    gui.py
    changelog.md
```

rather than a giant master template.

Then:

```python
render("context.py", ...)
render("cli.py", ...)
render("gui.py", ...)
```

Each template has one obvious purpose.

This maps beautifully onto your existing:

```text
scaffold/
    context.py
    cli.py
    gui.py
    changelog.py
```

architecture.

---

# 23. Don't put filesystem operations inside templates

Templates should not know that they are going into:

```text
src/cellshift/context.py
```

They just produce:

```python
Template(...)
```

The scaffold decides:

```python
destination = pyproject.src_dir / "context.py"
```

Then writes it.

That's another clean separation:

```text
Template
   ↓
str

Scaffold
   ↓
Path + str

Filesystem
   ↓
file
```

---

# 24. A good advanced pattern: immutable-ish rendering context

You can make a simple dataclass:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class TemplateContext:
    app_name: str
    pretty_name: str
    import_name: str
    description: str
```

Then turn it into the mapping expected by `Template`:

```python
context = TemplateContext(...)

template.substitute(vars(context))
```

This gives you:

- explicit fields
    
- type checking
    
- discoverability
    
- IDE support
    
- a stable contract
    

without introducing a template framework.

For your ecosystem, **this is probably the most interesting pattern beyond basic usage.**

---

# 25. Don't over-generalize the context

I wouldn't create:

```python
TemplateContext(
    everything=project.__dict__
)
```

Instead, let each scaffold construct the values it actually needs.

For example:

```python
context_values = {
    "app_name": pyproject.app_name,
    "import_name": pyproject.import_name,
    "description": pyproject.get("project", "description"),
}
```

This makes templates have small, understandable contracts.

---

# 26. Test templates independently

A good test looks like:

```python
def test_context_template():
    template = load_template("context.py")

    output = template.substitute(
        app_name="example",
        import_name="example",
        description="An example application",
    )

    assert 'APP_NAME = "example"' in output
    assert 'IMPORT_NAME = "example"' in output
```

Then your integration test can separately verify:

```text
init context
    ↓
actual file exists
    ↓
actual generated Python imports
```

That's much easier to debug than one giant scaffolding test.

---

# 27. Compile generated Python

For Python templates, there's a particularly nice second-level test:

```python
compile(output, "context.py", "exec")
```

You don't have to execute it.

This catches syntax errors introduced by your template.

For a scaffolding ecosystem, that's valuable:

```python
def test_context_template_is_valid_python():
    output = render_context(...)
    compile(output, "context.py", "exec")
```

---

# 28. Use `repr`-style formatting when inserting Python values

If you're generating Python source, don't do:

```python
Template("""
APP_NAME = "$app_name"
""")
```

if the value might contain quotes or special characters.

Instead, precompute a Python literal:

```python
Template("""
APP_NAME = $app_name_literal
""")
```

and:

```python
app_name_literal = repr(app_name)
```

giving:

```python
APP_NAME = 'CellShift'
```

This is a subtle but **very good** scaffolding practice.

You are generating source code, so generate syntactically valid literals rather than manually quoting arbitrary data.

---

# 29. Similarly, don't use templates to generate structured TOML if you don't need to

This is an important boundary.

For something like:

```text
pyproject.toml
```

if you're substantially constructing/modifying the document, a structured TOML API is preferable.

`Template` is excellent for:

> "Here is a mostly-static text artifact with a few substitutions."

It isn't intended to replace serializers.

So:

```text
README.md       → Template
cli.py          → Template
context.py      → Template
Flatpak file    → Template
pyproject.toml  → structured TOML manipulation
JSON            → json
```

That's a very healthy ecosystem.

---

# 30. The rule of thumb I'd use

### Use `string.Template` when:

> **80–95% of the output is fixed text and the rest is named substitution.**

### Use ordinary Python when:

> **the generation logic becomes conditional or algorithmic.**

### Use a serializer/parser when:

> **the output is fundamentally structured data.**

That gives you three tools, each doing one job.

---

# 31. Your current code maps very naturally onto this

Today you have:

```python
raw_context_str = """..."""
raw_context_str = raw_context_str.replace(
    "__IMPORT_NAME__",
    pyproject.import_name,
)
write_str_to_file(...)
```

A `string.Template` version becomes:

```python
template = Template("""...""")

text = template.substitute(
    import_name=pyproject.import_name,
)

write_str_to_file(
    pyproject.src_dir / "context.py",
    text=text,
)
```

And that's it.

**No new dependency. No framework. No abstraction tax.**

---

# 32. The "pro" end state I'd aim for

Not:

```text
Maxson Template Framework™
```

😄

Rather:

```text
maxson-build-utils
│
├── templates/
│   ├── context.py
│   ├── cli.py
│   ├── gui.py
│   └── ...
│
└── scaffold/
    ├── context.py
    ├── cli.py
    ├── gui.py
    └── ...
```

where a scaffold module is approximately:

```python
from string import Template

from ..helpers import write_str_to_file
from ..pyproject import PyProject


def run_init_context(root_dir=None):
    pyproject = PyProject(root_dir)

    template = Template(
        load_template("context.py")
    )

    text = template.substitute(
        app_name=pyproject.app_name,
        pretty_name=pyproject.pretty_name,
        import_name=pyproject.import_name,
        description=pyproject.get("project", "description"),
    )

    return write_str_to_file(
        pyproject.src_dir / "context.py",
        text=text,
    )
```

That is **tight, boring, testable, standard-library Python**.

And importantly, it leaves you plenty of room to discover what your scaffolding actually needs before introducing abstractions you don't yet need.

### Pocket reference

```python
from string import Template

template = Template("""
$app_name
${app_name}_config
$$100
""")

text = template.substitute(
    app_name="cellshift",
)

text = template.safe_substitute(...)

template.is_valid()
template.get_identifiers()
```

**Core rules:**

1. `$name` for substitutions.
    
2. `${name}` when boundaries matter.
    
3. `$$` for literal `$`.
    
4. Prefer `.substitute()` for scaffolding.
    
5. Treat `.safe_substitute()` as an intentional special case.
    
6. Keep logic in Python.
    
7. Keep templates mostly static.
    
8. Use structured serializers for structured data.
    
9. Keep template contexts explicit.
    
10. Test templates independently.
    
11. Compile generated Python in tests.
    
12. Don't subclass/customize `Template` until you have a concrete reason.
    

That gives us a very solid basis for looking at one of your currently empty scaffold modules next.

[[string Template usage! mbu, pass at pyproject toml]]
