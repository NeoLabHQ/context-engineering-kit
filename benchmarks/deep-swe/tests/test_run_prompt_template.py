#!/usr/bin/env python3
"""Unit tests for `run.py`'s prompt template: `render_prompt_template_text`
and the `NON_INTERACTIVE_CONTRACT` it appends to every arm.

The contract exists because the recorded run's agent ended its turn asking the
operator a multiple-choice question under `claude --print ... </dev/null`,
where nobody could answer. Three properties matter enough to pin:

1. Plugin arms still START with their slash command, or claude-code silently
   stops dispatching the skill and the arm quietly becomes a vanilla one.
2. `{{ instruction }}` survives, or pier refuses the template outright.
3. Plugin and vanilla arms carry the SAME contract text -- vanilla arms are the
   control this benchmark measures against, and prompt text present in one and
   absent from the other is a second, uncontrolled difference between them.

`run` is imported through `run_fixtures` -- see that module's docstring.
"""

from __future__ import annotations

import re
import unittest

from .run_fixtures import run


class NonInteractiveContractTests(unittest.TestCase):
    def test_every_arm_carries_the_contract(self) -> None:
        arms = run.build_arms(include_vanilla=True)
        self.assertEqual(len(arms), 13)
        for arm in arms:
            with self.subTest(arm=arm.id):
                self.assertIn(run.NON_INTERACTIVE_CONTRACT, run.render_prompt_template_text(arm))

    def test_plugin_and_vanilla_arms_carry_identical_contract_text(self) -> None:
        # Comparability: the two differ only by the invocation line.
        plugin = run.render_prompt_template_text(run.Arm("do-in-steps", "sonnet", "sonnet"))
        vanilla = run.render_prompt_template_text(run.Arm(None, "sonnet", None))
        plugin_contract = plugin.split("\n\n", 1)[1]
        vanilla_contract = vanilla.split("\n\n", 1)[1]
        self.assertEqual(plugin_contract, vanilla_contract)

    def test_the_contract_says_the_three_things_it_has_to_say(self) -> None:
        # Wording may be revised; these three claims may not quietly go missing.
        contract = run.NON_INTERACTIVE_CONTRACT.lower()
        self.assertIn("non-interactively", contract)
        self.assertIn("never end your turn with a question", contract)
        self.assertIn("choose the best available option", contract)

    def test_the_contract_contains_no_jinja_syntax(self) -> None:
        # It is spliced into a template body rendered under StrictUndefined; a
        # stray `{{` or `{%` would raise at run time, for every arm.
        self.assertNotIn("{{", run.NON_INTERACTIVE_CONTRACT)
        self.assertNotIn("{%", run.NON_INTERACTIVE_CONTRACT)


class TemplateShapeTests(unittest.TestCase):
    def test_a_plugin_arms_prompt_still_starts_with_its_slash_command(self) -> None:
        for arm in run.build_arms(include_vanilla=False):
            with self.subTest(arm=arm.id):
                first_line = run.render_prompt_template_text(arm).splitlines()[0]
                self.assertEqual(first_line, f"/{arm.skill} --model {arm.impl} {{{{ instruction }}}}")

    def test_a_vanilla_arms_prompt_starts_with_the_bare_instruction(self) -> None:
        rendered = run.render_prompt_template_text(run.Arm(None, "haiku", None))
        self.assertEqual(rendered.splitlines()[0], "{{ instruction }}")
        self.assertFalse(rendered.startswith("/"))

    def test_every_arm_keeps_the_instruction_variable_pier_requires(self) -> None:
        # pier's `render_prompt_template` rejects a template without it.
        for arm in run.build_arms(include_vanilla=True):
            with self.subTest(arm=arm.id):
                self.assertIn("{{ instruction }}", run.render_prompt_template_text(arm))

    def test_the_contract_follows_the_instruction_rather_than_preceding_it(self) -> None:
        rendered = run.render_prompt_template_text(run.Arm("do-and-judge", "opus", "sonnet"))
        self.assertLess(
            rendered.index("{{ instruction }}"), rendered.index(run.NON_INTERACTIVE_CONTRACT)
        )

    def test_no_arm_references_a_variable_pier_will_not_bind(self) -> None:
        """The StrictUndefined property, checked without jinja2 installed.

        This is Fix 2's highest-stakes property: pier renders these templates
        under `StrictUndefined` binding `instruction` alone, so a template
        naming anything else raises `UndefinedError` hours into a paid run. That
        makes it exactly the property that must not depend on a package the
        default test command lacks -- the jinja2 check below runs when it can,
        and this stdlib check always runs.

        Two ways a template can break the contract, both looked for here: a
        `{% ... %}` statement (blocks, loops, includes -- pier renders a bare
        string with one variable, so any of them is out of contract), and a
        `{{ ... }}` expression naming anything but `instruction`.
        """
        placeholder = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
        for arm in run.build_arms(include_vanilla=True):
            with self.subTest(arm=arm.id):
                body = run.render_prompt_template_text(arm)
                self.assertNotIn("{%", body)
                names = [match.strip() for match in placeholder.findall(body)]
                self.assertEqual(names, ["instruction"])

    def test_the_template_renders_with_jinja_under_strict_undefined(self) -> None:
        # The real thing when it is available: mirrors pier's own renderer
        # (jinja2 + StrictUndefined, binding only `instruction`). The stdlib
        # check above covers the same property when jinja2 is absent, so a
        # template regression cannot ship green either way.
        try:
            from jinja2 import Environment, StrictUndefined
        except ImportError:  # pragma: no cover -- depends on the interpreter
            self.skipTest("jinja2 is not installed; covered by the stdlib check above")

        environment = Environment(undefined=StrictUndefined)
        for arm in run.build_arms(include_vanilla=True):
            with self.subTest(arm=arm.id):
                template = environment.from_string(run.render_prompt_template_text(arm))
                rendered = template.render(instruction="Fix the failing tests.")
                self.assertIn("Fix the failing tests.", rendered)
                self.assertIn(run.NON_INTERACTIVE_CONTRACT, rendered)


if __name__ == "__main__":
    unittest.main()
