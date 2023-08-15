import typer
import subprocess
from rich import print as rprint
from typing_extensions import Annotated

app = typer.Typer()

MAIN_BRANCH_NAME = 'master'

def cmd(parts):
    return subprocess.run(parts, stdout=subprocess.PIPE).stdout.decode()

def pending_changes():
    result = cmd(['git', '--no-pager', 'diff'])
    if (result.strip() != ''):
        return True
    result = cmd(['git', '--no-pager', 'diff', '--staged'])
    if (result.strip() != ''):
        return True
    return False

def current_branch():
    return cmd(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()

def verify_no_pending_changes():
    if pending_changes():
        rprint('[red]Error: Pending changes.[red]')
        return False
    return True

def get_commits_in_branch(branch: str = ''):
    log = cmd(['git', 'rev-list', MAIN_BRANCH_NAME + '..' + branch])
    commits = log.split('\n')
    return commits[:-1]

def get_parent_commit_of_branch():
    commits_in_branch = get_commits_in_branch()
    parent = cmd(['git', 'log', '--pretty=%P', '-n', '1', commits_in_branch[0]])
    return parent.strip()

def num_commits_in_branch(branch: str = ''):
    return len(get_commits_in_branch(branch))
    
def get_commit_message(commit_hash: str):
    return cmd(['git', 'log', '--format=%B', '-n', '1', commit_hash]).strip()

def get_first_commit_on_branch(branch: str = ''):
    commits = get_commits_in_branch(branch)
    return commits[len(commits) - 1]

def squash_branch():
    num_commits = num_commits_in_branch()
    cmd(['git', 'reset', '--soft', 'HEAD~' + str(num_commits)])

def maybe_enable_auto_setup_remote():
    enabled = cmd(['git', 'config', 'push.autoSetupRemote']).strip()
    if (enabled != 'true'):
        cmd(['git', 'config', '--add', '--bool', 'push.autoSetupRemote', 'true'])

def all_branches():
    branches = cmd(['git', 'branch', '-a']).strip().split('\n')
    branches_canonical = []
    for branch in branches:
        branches_canonical.append(branch.strip().replace('* ', '').replace('remotes/origin/', ''))
    return set(branches_canonical)

def branch_is_descendant_of_current(branch: str):
    curr_branch = current_branch()
    cmd(['git', 'checkout', branch])
    commit = cmd(['git', 'rev-parse', 'HEAD']).strip()
    cmd(['git', 'checkout', curr_branch])
    descendants = cmd(['git', 'log', '--all', '--ancestry-path', curr_branch + '..'])
    if descendants.find(commit) > 0:
        return True
    return False

# Test Command
@app.command('test')
def test():
    print(cmd(['git', 'log', '--all', '--ancestry-path', current_branch() + '..']))

# New Command
@app.command('new')
def new(name: str, m: Annotated[str, typer.Option()] = ''):
    if name in all_branches():
        rprint('[red]Branch named "' + name + '" alreday exists.[red]')
        return
    if not verify_no_pending_changes():
        return
    message = m
    if message == '':
        message = name + ' <description pending>'
    maybe_enable_auto_setup_remote()
    cmd(['git', 'checkout', MAIN_BRANCH_NAME])
    cmd(['git', 'branch', name])
    cmd(['git', 'checkout', name])
    cmd(['git', 'commit', '--allow-empty', '-m', message])
    cmd(['git', 'push', '--force'])

# New Shorthand
@app.command('n')
def n(name: str, m: Annotated[str, typer.Option()] = ''):
    new(name, m)


# Open Command
@app.command('open')
def open(name: str):
    if not verify_no_pending_changes():
        return
    cmd(['git', 'checkout', name])

# Open shorthand
@app.command('o')
def o(name: str, m: Annotated[str, typer.Option()]):
    if not verify_no_pending_changes():
        return
    cmd(['git', 'checkout', name])


# Commit Command
@app.command('commit')
def create(reword: Annotated[str, typer.Option()] = ''):
    if current_branch() == MAIN_BRANCH_NAME:
        rprint('[red]pit cannot commit directly to branch ' + MAIN_BRANCH_NAME + '[red]')
        return
    message = reword
    if message == '':
        message = get_commit_message(get_first_commit_on_branch())
    maybe_enable_auto_setup_remote()
    cmd(['git', 'add', '-A'])
    cmd(['git', 'commit', '-m', '"pending squash"'])
    squash_branch()
    cmd(['git', 'commit', '--allow-empty', '-m', message])

# Commit Shorthand
@app.command('c')
def c(reword: Annotated[str, typer.Option()] = ''):
    create(reword)


# Upload Command
@app.command('upload')
def upload(reword: Annotated[str, typer.Option()] = ''):
    if current_branch() == MAIN_BRANCH_NAME:
        rprint('[red]pit cannot upload directly to branch ' + MAIN_BRANCH_NAME + '[red]')
    message = reword
    if message == '':
        message = get_commit_message(get_first_commit_on_branch())
    maybe_enable_auto_setup_remote()
    cmd(['git', 'add', '-A'])
    cmd(['git', 'commit', '-m', '"pending squash"'])
    squash_branch()
    cmd(['git', 'commit', '--allow-empty', '-m', message])
    cmd(['git', 'push', '--force'])

# Upload Shorthand
@app.command('u')
def u(reword: Annotated[str, typer.Option()] = ''):
    upload(u)


# Rebase Command
@app.command('rebase')
def rebase(branch: str):
    curr_branch = current_branch()
    if branch == curr_branch:
        rprint('Cannot rebase onto current branch')
        return
    if curr_branch == MAIN_BRANCH_NAME:
        rprint('[red]Cannot rebase ' + MAIN_BRANCH_NAME + '[red]')
        return
    if branch_is_descendant_of_current(branch):
        rprint('[red]Cannot rebase to descendant of self[red]')
        return
    old_base = get_parent_commit_of_branch()
    subprocess.run(['git', 'rebase', '--onto', branch, old_base, curr_branch])
    subprocess.run(['git', 'push', '--force'])
    subprocess.run(['git', 'push', '--force'])

# Rebase Shorthand
@app.command('r')
def r(branch: str):
    rebase(branch)


if __name__ == '__main__':
    app()