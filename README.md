# anomaly-detection
Anomaly detection in Real time monitoring

## development setup

### Windows install 
The quickest way is to install Anaconda (https://www.anaconda.com/products/individual) it contains all the required APIs

### Windows (wsl Ubuntu)

open terminal and run

```
sudo apt update && upgrade

sudo apt install python3 python3-pip ipython3

sudo apt install -y python3-venv

```

### Run Notebook 

In the project folder create local environment 

```
python3 -m venv localEnv

```

Activate local Env

```
source ./localEnv/bin/activate

```
Install library locally to localEnv

```
pip3 install -U wheel

python3 -m pip install -r requirements.txt

```
To run notebook

```
jupyter notebook --no-browser

```
