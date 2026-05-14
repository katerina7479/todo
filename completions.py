"""Shell completion script generation for the todo CLI."""

import todo as todo_module

# ---------------------------------------------------------------------------
# Dynamic helpers (called by the completion scripts at runtime)
# ---------------------------------------------------------------------------

def get_ids() -> list[str]:
    """Return all todo IDs (including done) as strings."""
    return [str(t["id"]) for t in todo_module.load_todos()]


def get_tags() -> list[str]:
    """Return sorted unique tag names across all todos."""
    seen: set[str] = set()
    for t in todo_module.load_todos():
        seen.update(t.get("tags", []))
    return sorted(seen)


# ---------------------------------------------------------------------------
# Bash completion script
# ---------------------------------------------------------------------------

_BASH_SCRIPT = """\
# Todo CLI bash completion
# Source this file or add to ~/.bash_completion.d/
#   eval "$(todo completions bash)"

_todo_completions() {{
    local cur prev subcommand
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    subcommand=""
    if [[ ${{COMP_CWORD}} -gt 1 ]]; then
        subcommand="${{COMP_WORDS[1]}}"
    fi

    if [[ ${{COMP_CWORD}} -eq 1 ]]; then
        COMPREPLY=($(compgen -W "{subcommands}" -- "${{cur}}"))
        return 0
    fi

    case "${{subcommand}}" in
        done|delete|show)
            local ids
            ids=$({prog} completions --list-ids 2>/dev/null)
            COMPREPLY=($(compgen -W "${{ids}}" -- "${{cur}}"))
            ;;
        list)
            if [[ "${{prev}}" == "--tag" ]]; then
                local tags
                tags=$({prog} completions --list-tags 2>/dev/null)
                COMPREPLY=($(compgen -W "${{tags}}" -- "${{cur}}"))
            else
                COMPREPLY=($(compgen -W "--all --tag" -- "${{cur}}"))
            fi
            ;;
        add)
            if [[ "${{prev}}" == "--tags" ]]; then
                local tags
                tags=$({prog} completions --list-tags 2>/dev/null)
                COMPREPLY=($(compgen -W "${{tags}}" -- "${{cur}}"))
            else
                COMPREPLY=($(compgen -W "--tags" -- "${{cur}}"))
            fi
            ;;
        search)
            COMPREPLY=()
            ;;
        completions)
            COMPREPLY=($(compgen -W "bash zsh" -- "${{cur}}"))
            ;;
        *)
            COMPREPLY=()
            ;;
    esac
    return 0
}}

complete -F _todo_completions {prog}
"""

# ---------------------------------------------------------------------------
# Zsh completion script
# ---------------------------------------------------------------------------

_ZSH_SCRIPT = """\
#compdef {prog}
# Todo CLI zsh completion
# Source this file or add to a directory in $fpath
#   eval "$(todo completions zsh)"

_todo_ids() {{
    local -a ids
    ids=($( {prog} completions --list-ids 2>/dev/null ))
    _values 'todo id' $ids
}}

_todo_tags() {{
    local -a tags
    tags=($( {prog} completions --list-tags 2>/dev/null ))
    _values 'tag' $tags
}}

_{prog}() {{
    local -a subcommands
    subcommands=(
        'add:Add a new todo item'
        'list:List todo items'
        'done:Mark a todo as done'
        'delete:Delete a todo item'
        'show:Show detail for a todo item'
        'search:Search todos by title or tag'
        'completions:Output shell completion script'
    )

    if (( CURRENT == 2 )); then
        _describe 'subcommand' subcommands
        return
    fi

    case "${{words[2]}}" in
        done|delete|show)
            _todo_ids
            ;;
        list)
            _arguments \\
                '--all[include completed todos]' \\
                '--tag[filter by tag]:tag:_todo_tags'
            ;;
        add)
            _arguments '--tags[comma-separated tags]:tags:_todo_tags'
            ;;
        completions)
            local -a shells
            shells=('bash:Bash completion script' 'zsh:Zsh completion script')
            _describe 'shell' shells
            ;;
        *)
            ;;
    esac
}}

_{prog} "$@"
"""

_SUBCOMMANDS = "add list done delete show search completions"


def bash_script(prog: str = "todo") -> str:
    return _BASH_SCRIPT.format(prog=prog, subcommands=_SUBCOMMANDS)


def zsh_script(prog: str = "todo") -> str:
    return _ZSH_SCRIPT.format(prog=prog)
