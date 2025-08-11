# Create a new directory for the function
mkdir -p ~/lambda_function
cd ~/lambda_function

# Create package directory
mkdir -p package

# Install only boto3
pip install boto3 --target package/

# Copy the Lambda function and utility files
cp /Users/svullam/git_projects/epic-web-app/backend/src/lambda/query_handler.py package/
mkdir -p package/utils
cp /Users/svullam/git_projects/epic-web-app/backend/src/utils/*.py package/utils/

# Create the deployment package
cd package
zip -r ../deployment.zip .

# Update the Lambda function
cd ..
aws lambda update-function-code --function-name book-qa-api-BookQALambda-lYarafs8YDZX --zip-file fileb://deployment.zip --region us-east-1
