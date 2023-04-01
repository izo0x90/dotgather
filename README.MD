# dotGather
```
                         ___      ,----..                  ___      ,---,                        
      ,---,            ,--.'|_   /   /   \               ,--.'|_  ,--.' |                        
    ,---.'|   ,---.    |  | :,' |   :     :              |  | :,' |  |  :                __  ,-. 
    |   | :  '   ,'\   :  : ' : .   |  ;. /              :  : ' : :  :  :              ,' ,'/ /| 
    |   | | /   /   |.;__,'  /  .   ; /--`    ,--.--.  .;__,'  /  :  |  |,--.   ,---.  '  | |' | 
  ,--.__| |.   ; ,. :|  |   |   ;   | ;  __  /       \ |  |   |   |  :  '   |  /     \ |  |   ,' 
 /   ,'   |'   | |: ::__,'| :   |   : |.' .'.--.  .-. |:__,'| :   |  |   /' : /    /  |'  :  /   
.   '  /  |'   | .; :  '  : |__ .   | '_.' : \__\/: . .  '  : |__ '  :  | | |.    ' / ||  | '    
'   ; |:  ||   :    |  |  | '.'|'   ; : \  | ," .--.; |  |  | '.'||  |  ' | :'   ;   /|;  : |    
|   | '/  ' \   \  /   ;  :    ;'   | '/  .'/  /  ,.  |  ;  :    ;|  :  :_:,''   |  / ||  , ;    
|   :    :|  `----'    |  ,   / |   :    / ;  :   .'   \ |  ,   / |  | ,'    |   :    | ---'     
 \   \  /               ---`-'   \   \ .'  |  ,     .-./  ---`-'  `--''       \   \  /           
  `----'                          `---`     `--`---'                           `----'            
```

Collection and dispersal script for configuration files, allowing you to manage the configurations for multiple machines in the same git repo.

Warning: Use at your own risk, someone probably did this in a better way and has a more mature project. I rolled my own because you know software people *shrug*.

## What it does:
- Allows to manage the configurations for many machines in one git repo

- Installs the script in a directory where gathered config files will be stored

- On setup init the directory with a git repo

- Create a subdir structure to store configuration files for the specific machine we are running on
  - The directory name is based on host by default (There is an option to override)

- Create a file with user inputted paths for configs that we want to target for collection  

- Gather target config files, new incoming changes can then be managed with git

- Disperse gathered configs to their target directories 
  - To clone machines configuration to other machines or recover to previous state etc.

- UNDO a disperse as long as target files have not changed since disperse

## Installation

Download the `dotgather.py` file to anylocation on your desired machine.

Execute the script in install mode with python and pass in the desired dir path for your new dotfile repo:
```
python3 ./dotgather.py --install INSTALL_DIR_PATH
```

To be able to run the script command without chaning to the repo dir:

- Add `INSTALL_DIR_PATH` to you system path
- Along with to you .rc file
  - Specific rc file depends on you chosen shell, if you are using a weird one env. var. syntax might be different, but if you are you already knew this
```
export DOTGATHERHOME=WHAT_EVER_YOUR_CHOSEN_DOTFILE_REPO_DIR_PATH
```

## Upgrade
Download a new version of `dotgather.py` file to anylocation on your desired machine.

Execute the script in install mode with python and pass in the desired dir path for your existing dotfile repo:
```
python3 ./dotgather.py --install INSTALL_DIR_PATH --upgragde
```

## Usage

### Setup dotfile management for a new machine
After installing run:
```
dg --setup
```

This will create the nessacry dir. structure and prompt you to input paths for the configs you want to target. 

You can also just skip the prompted input and just edit the `HOST_NAME_DIR/dotfilelist` file in you favorite editor. And you better be using Vim key-bindings!

### Gather
```
dg --gather
```

NOTE: Undos for the specific host/machine are removed on issuing a gather, it wouldn't make sense to have the undo and the currect source of truth for configuration to be the same.
If you want to implement more complex workflows use commits and git wisely to do so.

Review the pulled in changes using git, if everything looks good, commit and push to your preferred repo hub for backup.

### Disperse
```
dg --disperse
```

When cloning existing configs from another machnie to a new machine you will have to use the `--force-path` to select which sepecific set of configs from the multi machine repo you want to seed to the current machine.

### Undo
```
dg --undo-disperse
```

As long as something hasn't edited the target configs files since you dispersed them, and the undo hasn't been cleaned up you can restore the state of the target files to what it was prior to dispersion.

NOTE: Undos for the specific host/machine are removed on issuing a gather, it wouldn't make sense to have the undo and the currect source of truth for configuration to be the same.
If you want to implement more complex workflows use commits and git wisely to do so.

### Manually clean last disperse undo files for current host/machine
```
dg --clean
```

In general you shouldn't have to manually remove the undo files, but you have the option should that become needed.

### The `--force-path` option :feelsgood:

!!! Be very very careful with this one !!!

Aside from when you want to seed the config files from an exsiting machine to a new one you shouln'd really need to use the force path option.

Using force path can cause all kinds of state inconstencies with the script commands since their rulesets make certain assumptions. There are safeguards in the script to allow backup and prompt you when "funny" things are happaning, but in general you should really understand what steps a command takes and the full "state machine" if you are gonna use `--force-path` for anything other than seeding new machines with existing configs.


