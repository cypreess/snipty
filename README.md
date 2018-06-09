# snipty

Snipty is a handy package manager tool that helps you to organize snippets in the similar way how pip is 
handling python packages and ansible-galaxy is handling roles. The motivation behind snipty is to make 
snippets DRY again. There is a lot of good code too small to be legitimate packages on their own, that you 
end up copying over and over again to your codebase. Snipty wants to:

* automate the process of downloading snippets,
* create a `snippets.txt` file to explicitly enumerate your snippet dependencies in the code,
* allow easy tracking of snippets changes.

## Quickstart

### Single snippet installation

Install a single snippet into current directory project using providing path/name as destination:

    $ snipty install https://ghostbin.com/paste/egbue helpers/example_1
    ✔️ Snippet helpers/example_1 installed from https://ghostbin.com/paste/egbue
    
    $ ls helpers
    __init__.py  example_1.py
    
Note that your snippet will automatically have `.py` extension prepended and `__init__.py` files will be created
on all subdirectories up to the project root path, so your snippet will be importable from python.


### Handling requirements file

Snipty remembers what was installed (and where), by dumping some JSON into `.snipty` in your project 
root (current directory).


Create a `snippets.txt` files with snippets requirements:

    $ snipty freeze > snippets.txt
    
    $ cat snippets.txt
    helpers/example_1 from https://ghostbin.com/paste/egbue

Install snippets from `snippets.txt` file:

    $ snipty install -r snipty.txt
    $ Snippet 'helpers/example_1' has been already installed.

### Snippets with multiple files inside

Some snippet sites - like gist - allows you to define multiple files under a single URL. Snipty handles this by creating 
a directory (rather than a `.py` module file) and places all snippet files inside this directory.

Install snippets that have multiple files inside:

    $ snipty install https://gist.github.com/cypreess/6670a99b2c1cd7b52b24057f68a1debd helpers/django
    ✔️ Snippet helpers/django installed from https://gist.github.com/cypreess/6670a99b2c1cd7b52b24057f68a1debd
    
    $ ls helpers/django
    __init__.py  left_pad.py  middleware.py


### Deleting and moving snippets

Once snippet is installed it cannot be installed again to different location as snipty will warn you about 
possible code duplication.

    $ snipty install https://gist.github.com/cypreess/bc7b4d7c46b9a4cf1411c87b5c65d3d5 snippets/a
    ✔️ Snippet snippets/a installed from https://gist.github.com/cypreess/bc7b4d7c46b9a4cf1411c87b5c65d3d5
    
    $ snipty install https://gist.github.com/cypreess/bc7b4d7c46b9a4cf1411c87b5c65d3d5 snippets/b
    Error: Snippet 'snippets/a' has been already from the same source https://gist.github.com/cypreess/bc7b4d7c46b9a4cf1411c87b5c65d3d5.

To move snippet to other location simply delete the snippet from the previous location and reinstall snippet to 
another one (snipty will automatically detect this):

    $ snipty install https://gist.github.com/cypreess/bc7b4d7c46b9a4cf1411c87b5c65d3d5 snippets/a
    ✔️ Snippet snippets/a installed from https://gist.github.com/cypreess/bc7b4d7c46b9a4cf1411c87b5c65d3d5
    
    $ rm snippets/a.py
    
    $ snipty install https://gist.github.com/cypreess/bc7b4d7c46b9a4cf1411c87b5c65d3d5 snippets/b
    ✔ ️ Snippet snippets/b installed from https://gist.github.com/cypreess/bc7b4d7c46b9a4cf1411c87b5c65d3d5

### Snippets maintanance

To check if your snippets were updated comparing to what you have in your codebase you can simply run:

    $ snipty check --diff  https://gist.github.com/cypreess/6670a99b2c1cd7b52b24057f68a1debd snippets/left_pad
    ✔ Snippet snippets/left_pad present and up to date.

You can turn off diff displaying by adding argument `--diff`:

    snipty check --diff  https://gist.github.com/cypreess/6670a99b2c1cd7b52b24057f68a1debd snippets/left_pad
    ❌ Snippet snippets/left_pad file left_pad.py is not present.
    ❌ Snippet snippets/left_pad file middleware.py has changed.
      class EmptyMiddleware:
    +   middleware_empty = True
    -   pass

Check will produce exit status of 0 if all snippets are unchanged, otherwise exit status will be equal to number of 
changed snippets count.
    
## Helpful environment variables:

* `SNIPTY_PYTHON` - python interpreter that snipty should use to run itself
* `SNIPTY_ROOT_PATH` - default snipty behaviour is to treat all relative paths according to current directory; 
it can be ovveriden using this path or `-p`/`--path` argument
* `SNIPTY_TMP` - ovveride temporary directory for downloading snippets


## Help needed

Pull requests are very welcome.

- More downloaders needed
- Tests needed!
- Docs needed
