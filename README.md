# git-tools
Helpful tools for your GitLab projects (GitHub projects will be supported later).

## Development and installing
### Requirements
- GitLab access token with selected `api` scope
- Python >= 3.11.7
- `requirements-dev.txt`: contains linters, formatters and other libraries
needed for development
- `requirements-build.txt`: contains libraries for building a binary

```bash
# Create Python virtual environtment
python -m venv .venv
pip install -r requirements-dev.txt \
            -r requirements-build.txt
source .venv/bin/activate

# Create a git config where you store your access tokens
# from the provided .tokens.example
mkdir -p ~/.config/git/
cp .tokens.example ~/.config/git/.tokens
# Modify your .tokens file with your own values
```

### Code
Source files can be found in `src` of which `main.py` is where the base of `git-tools` 
is located, while `tools` is where each of those tools and other logic is.

To run without building, you must run the `src/main.py`:
```bash
PYTHONPATH="src/" python main.py  # help will be printed out for further usage
```

> [!NOTE]
> To be able to test the `show-issue` tool, you must run the above from a git project folder,
in which case, you might also have to adjust the `PYTHONPATH` to point to the `src/` folder
of this project.

#### Makefile
For easier development, you may also use the provided `Makefile` with its `make` targets:
```
❯ make
help                           Prints help for targets with comments
build                          Build git-tools binary
format                         Format using ruff
lint                           Lint using mypy and ruff
sanity                         Sanity check before formatting
```

### Building `git-tools`
To build the project, use the `make`:
```bash
make build
```

New folders with files will be generated (`build/`, `dist/`), of 
which `dist/` will contain the binary.

### Installing for global use
After building the project as shown above, add the following to your prefered 
shell config (`~/.bashrc`, `~/.zshrc`, etc.):
```bash
# adjust the path below to point to the ./dist folder here
export PATH=$PATH:"/path/to/git-tools/dist"
```

#### Example usage
![git-tools example usage](./git-tools.gif) 
