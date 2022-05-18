**0. Requirements**

*NOTE: Required essentials to get start*

    a. git
    b. Docker Engine (see https://docs.docker.com/engine/install/) (> version 20.10.5)
    c. Docker Compose (see https://docs.docker.com/compose/install/) (> version 1.29.2)
	
*NOTE: If using Windows*
	
	a. Git Bash for everything git-related (https://gitforwindows.org/)
	b. Docker Engine and Compose can be installed as a single package: https://www.docker.com/products/docker-desktop
	c. WSL2 for anything Docker-related (https://docs.microsoft.com/en-us/windows/wsl/install) (Remember to use WSL2-based engine in Docker)
	
**1. Clone SINTEF Co-Dev repository with MPC submodules**

    git clone --recurse-submodules -j8 ssh://git@git.code.sintef.no/sdfs/sintef-codev.git
    
    NOTE: For future pull, set the following flag to automatically update submodules

    git config --global submodule.recurse true

    To update all submodules manually

    git submodule update --recursive --remote

**2. Start up Docker compose orchastration (for local deployment)**


    In folder <path>/sintef-codev/docker/ run:
    export uid=$(id -u) gid=$(id -g) 
    docker-compose build

    In folder <path>/sintef-codev/docker/ run (terminal 1) (-d implies detached mode):
    docker-compose up -d

    To list and verify that all containers are running
    docker ps

    To terminate session 
    docker-compose down --remove-orphans

    To remove all countainers
    docker rm -f $(docker ps -a -q)

    Delete all volumes using the following command:
    docker volume rm $(docker volume ls -q)

    **DANGEROUS: Remove all resources**
    docker system prune -a 

**3. BACSSaaS ROME Server deployment (remote deployment)**

*NOTE: The user need to be on VPN or local SINTEF network to ssh into server*

    a. BACSSaaS has been deployed on SINTEF Digitals ROME server:

        IP: 129.241.64.67 
        USER: bacssaas
        PASSWORD: secret

    b. To conntect to Jupyter Notebook via some free local <PORT>:

        ssh bacssaas@129.241.64.67 -NL <PORT>:127.0.0.1:8888

    c. To access jupyter notebook, use the following in your browser:

        localhost:<PORT>

    d. Use the following token for login purposes, if prompter:

        docker log <CONTAINER ID>

        <ask phillip.maree@sintef.no for token>

**4. Visual Studio Code IDE (for local deployment)**

***Windows***
		
    1. Install Visual Studio Code (https://code.visualstudio.com/)  
    2. Install the following extenisons in Visual Code Studio:
        a. Docker    
        b. Remote - Containers
        c. Remote Development
        d. Python
    3. Attach Visual Studio Code to running container (i.e., bacssaas/mosiop:latest).
        a. F1 to search for commands, select: "Remote-Containers: Attach to Running Container".
        b. Select "bacssaas/mosiop:latest" from the drop-down menu.
    4. Create virtual python environment to prevent future package conflicts
        a. Open New Terminal 
        b. python3.9 -m venv .venv --system-site-packages			
        c. F1, "Python: Select Interpreter". Select the one in ./venv: Python 3.9.9 64-bit (./.venv/bin/python)
    5. For GUI-forwarding, this is a temporary solution:
        a. F1, select command "Remote-Containers: Add Attached Container Configuration File..."
        b. Select container "bacssaas/mosiop:latest".
        c. Add the following content, if not already there:
        {
          "workspaceFolder": "/home/bacssaas",
          "remoteEnv": {
             "DISPLAY": "host.docker.internal:0"
            }
        }
        d. Open new terminal, install Qt5:

            pip install pyqt5
        
        e. Get missing .so's (pip only install pure python. Maybe conda instead?):

            sudo apt-get install '^libxcb.*-dev' libx11-xcb-dev libglu1-mesa-dev libxrender-dev libxi-dev libxkbcommon-dev libxkbcommon-x11-dev
        
        f. Install VcXsrv: https://sourceforge.net/projects/vcxsrv/.
        g. Follow instructions for set up:
            https://techcommunity.microsoft.com/t5/windows-dev-appconsult/running-wsl-gui-apps-on-windows-10/ba-p/1493242

    6. Add Remote Container settings.json file
        a. File > Preferences > Settings
        b. Select Remote tab
        c. Open Extensions->Python->Edit in settings.json
        d Copy following content:
        {
            "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin",
            "python.pipenvPath": "${workspaceFolder}/.venv/bin",
            "python.envFile": "${workspaceFolder}/.env",
            "python.autoComplete.extraPaths": [
                "${workspaceFolder}/mosiop/lib"
            ],
            "terminal.integrated.defaultProfile.linux": "bash"
        }
    7. Add launch.json configation file
        a. Run->Add Configuration
        b. Copy the following content (os-independent launch-configuration with ${pathSeparator})
        {
            // Use IntelliSense to learn about possible attributes.
            // Hover to view descriptions of existing attributes.
            // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
            "version": "0.2.0",
            "configurations": [
            {
                "name": "Python: Current File",
                "type": "python",
                "request": "launch",
                "program": "${file}",
                "console": "integratedTerminal",
                "cwd": "${workspaceFolder}/${relativeFileDirname}",
                "env": {
                    "PYTHONPATH": "${workspaceFolder}${pathSeparator}${env:PYTHONPATH}"
                }         
            }
            ]
        }
    9. To test that the Python environment is working
        a. Open mosiop->lib->test->main.py
        b. Run->Run Without Debugging
        c. CSTR example should solve and display figures

***Linux***

    1. Install Visual Studio Code (https://code.visualstudio.com/)  
    2. Install the following extenisons in Visual Code Studio:
        a. Docker    
        b. Remote - Containers
        c. Remote Development
        d. Python
    3. Attach Visual Studio Code to running container (i.e., bacssaas/mosiop:latest).
    4. Create virtual python environment to prevent future package conflicts
        a. Open New Terminal 
        b. python3.9 -m venv .venv --system-site-packages
    5. Add Remote Container settings.json file
        a. File > Preferences > Settings
        b. Select Remote tab
        c. Open Extensions->Python->Edit in settings.json
        d Copy following content:
        {
            "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin",
            "python.pipenvPath": "${workspaceFolder}/.venv/bin",
            "python.envFile": "${workspaceFolder}/.env",
            "python.autoComplete.extraPaths": [
                "${workspaceFolder}/mosiop/opt"
            ],
            "terminal.integrated.defaultProfile.linux": "bash"
        }
    6. Add launch.json configation file
        a. Run->Add Configuration
        b. Copy the following content
        {
            // Use IntelliSense to learn about possible attributes.
            // Hover to view descriptions of existing attributes.
            // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "Python: Current File",
                    "type": "python",
                    "request": "launch",
                    "program": "${file}",
                    "console": "integratedTerminal",
                    "cwd": "${workspaceFolder}/${relativeFileDirname}",
                    "env": {
                    "PYTHONPATH": "${workspaceFolder}/mosiop/"
                    }        
                }
            ]
        }
    7. To test that the Python environment is working
        a. Open mosiop->lib->test->main.py
        b. Run->Run Without Debugging
        c. CSTR example should solve and display figures

**5. Visual Studio Code IDE (with remote deployment)**

*NOTE: The user need to be on VPN or local SINTEF network to ssh into server*

***Linux***

    1. Install Visual Studio Code (https://code.visualstudio.com/)
    2. Install the following extenisons in Visual Code Studio:
        a. Remote - SSH
        b. Remnote - SSH: Editing Configuation Files
        c. Docker    
        d. Remote - Containers
        e. Remote Development
        f. Python
    3. Create a new Connect to Host configuration. The following should be added to your /homw/<user>/.ssh/config file: 
        
        Host BACSSaaS
            HostName 129.241.64.67
            User bacssaas
    4. Coneect to host BACSSaaS
    5. To verify connection and running BACSSaaS containers:
        a. Open terminal window Terminal->New Terminal
        b. Type
            docker ps

***Windows***

    1. Install Visual Studio Code (https://code.visualstudio.com/) 
    2. Install the following Visual Studio Code extensions:
        a. Remote - SSH
        b. Remnote - SSH: Editing Configuation Files
        c. Docker    
        d. Remote - Containers
        e. Remote Development
        f. Python
    3. Connect to remote BACSSaaS host on ROME server:
        a. Open a remote window (greeen icon bottom-left)
        b. Open SSH Configuration File (i.e., C:\Users\<user>\.ssh\config) and update with:
            Host BACSSaaS
                HostName 129.241.64.67
                User bacssaas
        c. Save config file (ctrl+s)
        d. Open a remote window -> Connect Current Window to Host -> BCASSaaS
        e. The platform for remote host "BACSSaaS" is linux
        f. Open Visual Studio Code workspace <bacssass.code-workspace>
        



        



    
    



	


