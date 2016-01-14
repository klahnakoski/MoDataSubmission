#
# WARNING:  Do not use this script directly.  Think of it as an installation guide.
#

sudo -i
export PYTHONPATH=.
export HOME=/home/ec2-user
cd ~/MoDataSubmission
git pull origin master
nohup python27 modatasubmission/app.py --settings=resources/config/prod.json &

disown -h
