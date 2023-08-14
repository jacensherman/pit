import typer
import subprocess
from rich import print as rprint
from typing_extensions import Annotated

app = typer.Typer()

def pending_changes():
    result = subprocess.run(['git', 'diff-index', 'HEAD', '--'], stdout=subprocess.PIPE)
    if (result.stdout == b''):
        return False
    return True

def verify_no_pending_changes():
    if pending_changes():
        rprint('[red]Error: Pending changes.[red]')
        return False
    return True

def get_commits_in_branch(branch: str = ''):
    log = subprocess.run(['git', 'rev-list', 'main..' + branch], stdout=subprocess.PIPE).stdout.decode()
    commits = log.split('\n')
    return commits[:-1]

def num_commits_in_branch(branch: str = ''):
    return len(get_commits_in_branch(branch))
    
def get_commit_message(commit_hash: str):
    return subprocess.run(['git', 'rev-list', '--format=%B', '--max-count=1', commit_hash], stdout=subprocess.PIPE).stdout.decode()

def get_first_commit_on_branch(branch: str = ''):
    commits = get_commits_in_branch(branch)
    return commits[len(commits) - 1]

def squash_branch():
    num_commits = num_commits_in_branch()
    subprocess.run(['git', 'reset', '--soft', 'HEAD~' + str(num_commits)])

# Test Command
@app.command('test')
def test():
    get_commit_message(get_first_commit_on_branch())


# New Command
@app.command('new')
def new(name: str, m: Annotated[str, typer.Option()]):
    if not verify_no_pending_changes():
        return
    subprocess.run(['git', 'checkout', 'main'])
    subprocess.run(['git', 'branch', name])
    subprocess.run(['git', 'checkout', name])
    subprocess.run(['git', 'commit', '--allow-empty', '-m', '"' + m + "'"])
    subprocess.run(['git', 'push', '--force', '--set-upstream', 'origin', 'main'])

# New Shorthand
@app.command('new')
def n(name: str, m: Annotated[str, typer.Option()]):
    new(name, m)


# Open Command
@app.command('open')
def open(name: str, m: Annotated[str, typer.Option()]):
    if not verify_no_pending_changes():
        return
    subprocess.run(['git', 'checkout', name])

# Open shorthand
@app.command('o')
def o(name: str, m: Annotated[str, typer.Option()]):
    if not verify_no_pending_changes():
        return
    subprocess.run(['git', 'checkout', name])


# Commit Command
@app.command('commit')
def create(reword: Annotated[str, typer.Option()] = ''):
    message = reword
    if message == '':
        message = get_commit_message(get_first_commit_on_branch())
    num_commits = num_commits_in_branch()
    subprocess.run(['git', 'add', '-A'])
    subprocess.run(['git', 'reset', '--soft', 'HEAD~' + str(num_commits)])
    subprocess.run(['git', 'commit', '--allow-empty', '-m', '"' + message + "'"])

# Commit Shorthand
@app.command('c')
def c(reword: Annotated[str, typer.Option()] = ''):
    create(reword)


# Upload Command
@app.command('upload')
def upload(reword: Annotated[str, typer.Option()] = ''):
    message = reword
    if message == '':
        message = get_commit_message(get_first_commit_on_branch())
    num_commits = num_commits_in_branch()
    subprocess.run(['git', 'add', '-A'])
    subprocess.run(['git', 'reset', '--soft', 'HEAD~' + str(num_commits)])
    subprocess.run(['git', 'commit', '--allow-empty', '-m', '"' + message + "'"])
    subprocess.run(['git', 'push', '--force'])

# Upload Shorthand
@app.command('u')
def u(reword: Annotated[str, typer.Option()] = ''):
    upload(u)


# Sync Command
@app.command('sync')
def sync():
    subprocess.run(['git', 'rebase', '-i', 'main'])

@app.command('s')
def s():
    sync()


# Rebase Command
@app.command('rebase')
def rebase(branch: str):
    subprocess.run(['git', 'rebase', '-i', branch])

@app.command('r')
def r(branch: str):
    rebase(branch)

if __name__ == '__main__':
    app()