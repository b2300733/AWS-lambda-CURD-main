#!/bin/bash
#sudo pip3 install boto3

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR" || exit 1

echo Please enter a valid IP address:
read ip_address
echo IP address:$ip_address
AWS_REGION="us-east-1"
bucket=`aws s3api list-buckets --query "Buckets[].Name" | grep s3bucket | tr -d ',' | sed -e 's/"//g' | xargs`
echo $bucket

echo "export bucket=$bucket" >> "$HOME/.bashrc"
echo "export bucket_url=\"https://${bucket}.s3.${AWS_REGION}.amazonaws.com/index.html\"" >> "$HOME/.bashrc"
FILE_PATH="$SCRIPT_DIR/website_security_policy.json"
FILE_PATH_2="$SCRIPT_DIR/permissions.py"


aws s3 cp "$SCRIPT_DIR/website" "s3://$bucket/" --recursive --cache-control "max-age=0"

sed -i "s/<FMI_1>/$bucket/g" $FILE_PATH_2

sed -i "s/<FMI_1>/$bucket/g" $FILE_PATH
sed -i "s/<FMI_2>/$bucket/g" $FILE_PATH
sed -i "s/<FMI_3>/$ip_address/g" $FILE_PATH

python3 "$SCRIPT_DIR/permissions.py"
python3 "$SCRIPT_DIR/seed.py"