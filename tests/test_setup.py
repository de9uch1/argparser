import json

import argparser.app
import pytest


@pytest.mark.parametrize("prog", ["prog", ""])
@pytest.mark.parametrize("desc", ["This is a description.", ""])
@pytest.mark.parametrize("epilog", ["This is a epilog.", ""])
def test_setup(capfd: pytest.CaptureFixture, prog: str, desc: str, epilog: str):

    argparser.app.main(["setup", prog, desc, epilog])
    out, err = capfd.readouterr()

    expected = {"__metatype": "setup"}
    if prog:
        expected["prog"] = prog
    if desc:
        expected["description"] = desc
    if epilog:
        expected["epilog"] = epilog

    assert json.loads(out) == expected
    assert err == ""
