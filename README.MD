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

## Usage
