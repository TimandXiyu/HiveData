# HiveDataDump
Dump the mining speed data from hiveon pool to local disk

### To setup env  
You need venv or conda.
You can install conda by downloading the setup file here: https://www.anaconda.com/products/individual  
To setup the env:  
You need to first   
`conda crate -n "the_env_name" python=3.7`  
Then  
`conda activate the_env_name`  
Then  
`pip install -r requirements`  


### To change the trigger date, you just need to change the line 11 in Scheduler.py

### To pack the scripts yourself
`pyinstaller --one-file Scheduler.py`  

