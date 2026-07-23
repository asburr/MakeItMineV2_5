# argparse
```python
import argparse

main_p = argparse.ArgumentParser()

# Add arguments to main
main_p.add_argument("-v")

# Add subcommands to main
main_s_p = main_p.add_subparsers(help='commands')

# Add a command git to main
git_p = main_s_p.add_parser("git")

# Add arguments to git
git_p.add_argument("-x")

# Add subcommands to git
git_s_p = git_p.add_subparsers(help='commands')

# Add a sub command
pull_p = git_s_p.add_parser("pull")

# Add arguments to pull
pull_p.add_argument("-x")

```