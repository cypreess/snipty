# snipty

Snipty is a handy package manager tool that allows to organize snippets in the simmilar way how pip is handling python packages and ansible-galaxy is handling roles. The motivation behind snipty is to make snippets DRY again. There is lots of good code to small to be legitimate packages on their own that you end up copy over and over again to your codebase. Snipty wants to:

* automate the process of downloading them,
* create a `snippets.txt` file to explicitly enumarate your snippet dependencies in the code,
* allow easy tracking of snippets changes.
