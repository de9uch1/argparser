import json
from typing import Any, Dict, List

import argparser.app
import pytest


@pytest.mark.parametrize(
    "flags",
    [["opt"], ["--long", "long-option"], ["--short", "o"], ["-l", "opt", "-s", "o"]],
)
@pytest.mark.parametrize("required", ["--required", ""])
@pytest.mark.parametrize("action", [["--action", "store_true"], []])
@pytest.mark.parametrize("desc", [["--desc", "help messeage"], []])
@pytest.mark.parametrize("type", [["--type", "int"], []])
@pytest.mark.parametrize("default", [["--default", "3"], []])
@pytest.mark.parametrize("nargs", [["--nargs", "*"], []])
@pytest.mark.parametrize("choices", [["--choices", "1", "2"], []])
def test_add(
    capfd: pytest.CaptureFixture,
    flags: List[str],
    required: str,
    action: List[str],
    desc: List[str],
    type: List[str],
    default: List[str],
    nargs: List[str],
    choices: List[str],
):
    varname = "VAR"

    argv = ["add", varname]
    argv += flags
    argv.append(required)
    argv += action
    argv += desc
    argv += type
    argv += default
    argv += nargs
    argv += choices

    argparser.app.main(argv)
    out, err = capfd.readouterr()

    expected: Dict[str, Any] = {"__metatype": "arg", "varname": varname}

    if any(arg.startswith("-") for arg in flags):
        assert len(flags) % 2 == 0
        flags_val = []
        for i in range(0, len(flags), 2):
            if flags[i] in {"--long", "-l"}:
                flags_val.append("--" + flags[i + 1])
            elif flags[i] in {"--short", "-s"}:
                flags_val.append("-" + flags[i + 1])
            else:
                raise NotImplementedError
        expected["flags"] = flags_val
        expected["required"] = required == "--required"
    else:
        expected["flags"] = flags

    if action:
        expected["action"] = action[1]
    if desc:
        expected["help"] = desc[1]
    if type:
        expected["type"] = type[1]
    else:
        expected["type"] = "str"
    if default:
        expected["default"] = default[1]
    if nargs:
        expected["nargs"] = nargs[1]
    if choices:
        expected["choices"] = choices[1:]

    assert json.loads(out) == expected
    assert err == ""
