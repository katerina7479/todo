vagrant_ubuntu14_shell
======================

Virtual development environment, with no virtualenv required.
You can deploy your project to other providers by changing the 
Vagrantfile. No puppet, no chef, just simple shell scripts.

On Host computer, it requires Vagrant, Virtualbox, Git, and a good internet connection.
Simply clone this repo, cd to the Vagrantfile, and do:

`> vagrant up`

Vagrant will build a virtualbox virtual machine, with ubuntu trusty 14.04. It installs
git, pip, and uses pip to install anything you've defined in requirements.txt. It may 
take longer the first time, but after, will store the base box, so not as slow the second.

To access do:

`> vagrant ssh`

Your shared folder is in the "home\vagrant\projects" folder. You can use your text editor on your host computer to
make changes, and run your program in the virtual env. 

If you want to throw it away, do:

`> vagrant destroy`

Look at the [vagrant docs](https://docs.vagrantup.com/v2/) for more information.