#
# WARNING:  Do not use this script directly.  Think of it as an installation guide.
#

sudo -i
export PYTHONPATH=.
export HOME=/home/ec2-user
cd ~/MoDataSubmission
git checkout master
git pull origin master


#exec -a "MoDataSubmission" python27 modatasubmission/app.py --settings=resources/config/prod.json
nohup python27 modatasubmission/app.py --settings=resources/config/prod.json &
disown -h
