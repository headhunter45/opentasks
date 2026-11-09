# Changes for version v0.1.4

- Use `CHANGELOG.md` for GitHub Release notes and display release notes on the website (`f52a8f`).
- Allow `ot task create "<title>"` with a positional title argument to work identically to `ot task create -m "<title>"` (`2f1455`).
- Add `ot task update <id>` subcommand to update WorkItem frontmatter fields and overview via CLI flags (`efd404`).
- Make default output width 120 columns (using full terminal width when `>= 120` and `80` when `< 120`) and add `--width` override (`dd2649`).
- Support filtering `ot task list` by multiple columns, repeatable/comma-separated column values, and value prefixes (`984260`).
- Add `--id` and `--title` filters, `--type`/`--status` allowed-value validation, and `--author` substring/`/regex/` matching to `ot task list` (`229d60`).
