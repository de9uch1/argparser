import argparse
import json
import shlex
import sys
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, Optional, Sequence


class ArgumentParserWrapper(ArgumentParser):
    def _print_message(self, message, file=None):
        if message:
            sys.stderr.write(message)

    def exit(self, status=1, message=None):
        if message:
            self._print_message(message, sys.stderr)
        print(f"exit {status}")
        sys.exit(status)


class HelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.MetavarTypeHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    def _format_action(self, action):
        # determine the required width and the entry label
        help_position = min(self._action_max_length + 2, self._max_help_position)
        help_width = max(self._width - help_position, 11)
        action_width = help_position - self._current_indent - 2
        action_header = self._format_action_invocation(action)

        # no help; start on same line and add a final newline
        if not action.help:
            tup = self._current_indent, "", action_header
            action_header = "%*s%s\n" % tup

        # short action name; start on the same line and pad two spaces
        elif len(action_header) <= action_width:
            tup = self._current_indent, "", action_width, action_header
            action_header = "%*s%-*s  " % tup
            indent_first = 0

        # long action name; start on the next line
        else:
            tup = self._current_indent, "", action_header
            action_header = "%*s%s\n" % tup
            indent_first = help_position

        # collect the pieces of the action help
        parts = [action_header]

        # if there was help for the action, add lines of help text
        if action.help:
            help_text = self._expand_help(action)
            if help_text:
                help_lines = self._split_lines(help_text, help_width)
                parts.append("%*s%s\n" % (indent_first, "", help_lines[0]))
                for line in help_lines[1:]:
                    parts.append("%*s%s\n" % (help_position, "", line))

        # or add a newline if the description doesn't end with one
        elif not action_header.endswith("\n"):
            parts.append("\n")

        # if there are any sub-actions, add their help as well
        for subaction in self._iter_indented_subactions(action):
            parts.append(self._format_action(subaction))

        # return a single string
        return self._join_parts(parts)


def strtobool(val: str) -> bool:
    """Convert a string representation of truth to true or false.

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.
    Raises ValueError if 'val' is anything else.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError("invalid truth value {!r}".format(val))


def add(args: Namespace):
    parser_args: Dict[str, Any] = {"__metatype": "arg"}
    parser_args["varname"] = args.varname

    if args.position is not None:
        parser_args["flags"] = [args.position]
    else:
        flags = []
        if args.long:
            flags.append(f"--{args.long}")
        if args.short:
            flags.append(f"-{args.short}")
        parser_args["flags"] = flags
        parser_args["required"] = args.required

    if args.action:
        parser_args["action"] = args.action
    if args.desc:
        parser_args["help"] = args.desc
    if args.type:
        parser_args["type"] = args.type
    else:
        parser_args["type"] = "str"
    if args.default:
        parser_args["default"] = args.default
    if args.nargs:
        parser_args["nargs"] = args.nargs
    if args.choices:
        parser_args["choices"] = args.choices

    print(json.dumps(parser_args))


def setup(args: Namespace):
    parser_args: Dict[str, Any] = {"__metatype": "setup"}
    if args.prog:
        parser_args["prog"] = args.prog
    if args.desc:
        parser_args["description"] = args.desc
    if args.epilog:
        parser_args["epilog"] = args.epilog
    print(json.dumps(parser_args))


def parse(args):
    varnames = []
    parser = ArgumentParserWrapper(formatter_class=HelpFormatter)
    for l in sys.stdin:
        item = json.loads(l.strip())

        if item["__metatype"] == "setup":
            if "prog" in item:
                parser.prog = item["prog"]
            if "description" in item:
                parser.description = item["description"]
            if "epilog" in item:
                parser.epilog = item["epilog"]

        elif item["__metatype"] == "arg":
            flags = item["flags"]
            varnames.append(item["varname"])
            for k in ["flags", "varname", "__metatype"]:
                del item[k]

            if item.get("action", "") == "store_true":
                item["default"] = False
                if "type" in item:
                    del item["type"]
                if "help" not in item:
                    item["help"] = " "
            if item.get("action", "") == "store_false":
                item["default"] = True
                if "type" in item:
                    del item["type"]
                if "help" not in item:
                    item["help"] = " "

            if "type" in item:
                item_type = eval(item["type"])
                if item_type is bool:
                    item["type"] = strtobool
                else:
                    item["type"] = item_type

            if "default" in item and "type" in item:
                item["default"] = item["type"](item["default"])
                if "help" not in item:
                    item["help"] = " "
            if "choices" in item and "type" in item:
                item["choices"] = list(map(item["type"], item["choices"]))

            parser.add_argument(*flags, **item)

    parsed_args = parser.parse_args(sys.argv[2:])
    for name, v in zip(varnames, vars(parsed_args).values()):
        if v is None:
            continue
        elif isinstance(v, list):
            v_str = shlex.join(map(str, v))
            print(f"{name}=({v_str})")
        elif isinstance(v, bool):
            print(f"{name}={str(v).lower()}")
        else:
            print(f"{name}={shlex.quote(str(v))}")


def usage(args: Namespace):
    s = r"""Argument parser for shell script.

USAGE:
    1. Define add_args() function and add arguments.
    2. The first argument of `argparser add` is a variable name in the script which will
       be set to the given argument value.
    3. The second positional argument, --long/-l and --short/-s options will be
       command line argument names.
    4. Other arguments of `argparser add` can be shown by `argparser add --help`.
    5. `eval $(add_args | argparser parse "$@")` parses command line arguments.

EAMPLE:
    --------------------------------------------------------
    #!/bin/bash

    function add_args() {
        argparser setup --prog "$0" --desc "Test script."
        argparser add FILE        file
        argparser add WORKERS  -l num-workers  -s n --type int --default 8
        argparser add USER_IDS -l user-ids     -s u --type int --nargs "*"
        argparser add BETA     -l experimental      --action store_true
        argparser add LANGUAGE -l lang              --choices en de ja
    }

    eval $(add_args | argparser parse "$@")
    --------------------------------------------------------

    $ ./test.sh --file log.txt --num-workers 16 -u 100 200 --experimental --lang ja

    The variables in the script will be set to:
        - FILE=log.txt
        - WORKERS=16
        - USER_IDS=(100 200)  # Stored in array
        - BETA=true           # This is helpful for such situation: `if $BETA; then ...`
        - LANGUAGE=ja

    You can also see the help messages by `./test.sh --help`.

NOTE:
    - This software was inspired by https://github.com/ko1nksm/getoptions
"""
    print(s)


def main(argv: Optional[Sequence[str]] = None):
    parser = ArgumentParser(description="Argument parser for shell script.")
    subparsers = parser.add_subparsers()
    help_parser = subparsers.add_parser(
        "help", help="Show details of usage and an example."
    )
    help_parser.set_defaults(func=usage)

    setup_parser = subparsers.add_parser(
        "setup", help="Setup a header and footer of the help message."
    )
    # fmt: off
    setup_parser.add_argument("--prog", type=str,
                            help="Program name. Usually $0 should be given.")
    setup_parser.add_argument("--desc", type=str,
                            help="Description.")
    setup_parser.add_argument("--epilog", type=str,
                            help="Epilog.")
    # fmt: on
    setup_parser.set_defaults(func=setup)

    add_parser = subparsers.add_parser("add", help="Define arguments.")
    # fmt: off
    add_parser.add_argument("varname", type=str,
                            help="Variable name.")
    add_parser.add_argument("--long", "-l", type=str,
                            help="Long option without prefix hyphens.")
    add_parser.add_argument("--short", "-s", type=str,
                            help="Short option without a prefix hyphen.")
    add_parser.add_argument("position", nargs="?", type=str,
                            help="Positional argument.")
    add_parser.add_argument("--desc", type=str,
                            help="Help message.")
    add_parser.add_argument("--type", "-t", type=str,
                            help="Type of an argument.")
    add_parser.add_argument("--default", type=str,
                            help="Default value.")
    add_parser.add_argument("--action", type=str,
                            help="Action.")
    add_parser.add_argument("--nargs", type=str,
                            help="Number of arguments. *, ?, and + can be specified.")
    add_parser.add_argument("--required", action="store_true",
                            help="Set the option as required.")
    add_parser.add_argument("--choices", nargs="+",
                            help="Choice from a restricted set of values.")
    # fmt: on
    add_parser.set_defaults(func=add)

    parse_parser = subparsers.add_parser(
        "parse",
        add_help=False,
        help="Parse command line arguments. "
        'This subcommand is only called by `eval $(add_args | argparser parse "$@")` '
        "in a shell script with a defined `add_args()` function. "
        "See an example by `argparser help`.",
    )
    parse_parser.set_defaults(func=parse)
    args, _ = parser.parse_known_args(argv)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
