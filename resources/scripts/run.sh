
sudo -i
export PYTHONPATH=.
export HOME=/home/ec2-user
cd ~/MoDataSubmission
nohup python27 modatasubmission/app.py --settings=resources/config/prod.json
disown -h
