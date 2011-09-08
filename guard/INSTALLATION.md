# How to install and run Guard

## Ruby
 - Guard uses Ruby. OS X comes bundled with Version 1.8.7 which is enough for basic daily usage.
 - If you are on a different platform, or want to compile Ruby from source, go and get it from [here](http://www.ruby-lang.org/en/downloads/).
 - If you want to manage multiple versions of Ruby check out [RVM](http://beginrescueend.com/).
 - If you have questions or need help getting Ruby up and running on your System ask [Me](mailto:rodrigo@codegestalt.com).

## Installing Guard

### On Mac OS X
 - Run `sudo gem install guard guard-shell rb-fsevent` in the command line. This will install all dependencies for OS X and the basic guard gem.
 - If you use Growl you can enable notifications by installing the growl notify gem: `sudo gem install growl_notify`

### On Linux
 - Run `sudo gem install guard guard-shell rb-inotify` in the command line. This will install all dependencies for Linux and the basic guard gem.

### On Windows
 - Run `gem install guard guard-shell rb-fchange` in a command prompt. This will install all dependencies for Windows and the basic guard gem.


## Using Guard
Guard uses so called "guards" for specific tasks. If you want to compile a SASS file into CSS for example you could use the "guard-sass" guard and add it to your guardfile.
If you just want to run custom shell scripts use "guard-shell" and add it to your guardfile. You can find a list of all available guards [here](https://github.com/guard/guard/wiki/List-of-available-Guards).

### Basic usage
  1. Edit the provied Guardfile to your liking and add it to the directory that should be watched.
  2. In the Guardfile directory run `guard` in the command line.
  3. Guard will now watch for any filesystem changes that you have specified in the Guardfile and execute all configured commands.
