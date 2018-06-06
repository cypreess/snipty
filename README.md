# snipty

Snipty is a handy package manager tool that allows to organize snippets in the similar way how pip is 
handling python packages and ansible-galaxy is handling roles. The motivation behind snipty is to make 
snippets DRY again. There is lots of good code to small to be legitimate packages on their own that you 
end up copy over and over again to your codebase. Snipty wants to:

* automate the process of downloading them,
* create a `snippets.txt` file to explicitly enumerate your snippet dependencies in the code,
* allow easy tracking of snippets changes.

## Quickstart

Install a single snippet into current directory project:

    $ snipty install https://ghostbin.com/paste/egbue helpers/example_1
    ✔️ Snippet helpers/example_1 installed from https://ghostbin.com/paste/egbue

    
Create a `snippets.txt` files with snippets requirements:

    $ snipty freeze > snippets.txt
    $ cat snippets.txt
    helpers/example_1 from https://ghostbin.com/paste/egbue

Install snippets from `snippets.txt` file:

    $ snipty install -r snipty.txt
    $ Snippet 'helpers/example_1' has been already installed.


Snipty remembers what was installed (and where), by dumping some JSON into `.snipty` in your project 
root (current directory). You probably want to add this file to `.gitignore`.


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
