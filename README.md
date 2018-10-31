# snipty  [![CircleCI](https://circleci.com/gh/cypreess/snipty/tree/master.svg?style=svg)](https://circleci.com/gh/cypreess/snipty/tree/master)


Snipty is a handy "like a package manager" tool that helps you to keep track of code snippets in a codebase.

The motivation behind Snipty is to make 
snippets DRY again. There is a lot of good code too small to be legitimate packages on their own, that you 
end up copying over and over again to your codebase. Snipty wants to:

* automate the process of downloading snippets from remote snippet websites,
* manage a `snipty.yml` file to explicitly enumerate your snippet dependencies in the code,
* allow easy tracking of snippets changes when they are made in your codebase and/or in the snippet source.

You can read about [how Snipty was born and what problem it tries to address](https://medium.com/@krisdorosz/how-to-use-code-snippets-and-stay-sane-987a2a54c571) in the Medium post.

## Quickstart

### Snippet installation

We assume you store snippets somewhere in the snippets websites (like Github gist or ghostbin).
To install snippet in your code base go to the codebase root and type:

    $ snipty install  helpers/example_1.py https://ghostbin.com/paste/egbue
    ✔️ Snippet helpers/example_1 installed from https://ghostbin.com/paste/egbue
    
    $ ls helpers
    __init__.py  example_1.py
    
Snipty detects that this is python snippet (by given extension) 
and automatically creates  `__init__.py` on all subdirectories up to the project root path,
so your snippet will be importable from python.


At this point a special file `snipty.yml` was created in your codebase. You should track this file in your
code versioning system.


### Snippets with multiple files inside

Some snippet sites - like gist - allows you to define multiple files under a single URL. Snipty handles this by creating 
a directory (rather than a single file) and places all snippet files inside this directory.

Install snippets that have multiple files inside:

    $ snipty install helpers/django https://gist.github.com/cypreess/6670a99b2c1cd7b52b24057f68a1debd 
    ✔️ Snippet helpers/django installed from https://gist.github.com/cypreess/6670a99b2c1cd7b52b24057f68a1debd
    
    $ ls helpers/django
    __init__.py  left_pad.py  middleware.py


### Deleting and moving snippets

Once snippet is installed it cannot be installed again to different location as snipty will warn you about 
possible code duplication.

    $ snipty install snippets/a https://gist.github.com/cypreess/bc7b4d7c46b9a4cf1411c87b5c65d3d5 
    ✔️ Snippet snippets/a installed from https://gist.github.com/cypreess/bc7b4d7c46b9a4cf1411c87b5c65d3d5

    $ snipty install snippets/a https://gist.github.com/cypreess/bc7b4d7c46b9a4cf1411c87b5c65d3d5 
    Snippet 'snippets/a' has been already installed.


### Snippets maintenance

To check if your snippets in your codebase differ from the remote links type:

    $ snipty check 
    ✔ Snippet snippets/left_pad present and up to date.

or for single package:

    $ snipty check snippets/left_pad
    ✔ Snippet snippets/left_pad present and up to date.

You can turn on diff displaying by adding argument `--diff`:

    snipty check --diff snippets/left_pad
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
