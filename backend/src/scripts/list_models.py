import boto3

def list_models():
    """List available Bedrock models."""
    bedrock = boto3.client('bedrock', region_name='us-east-1')
    try:
        response = bedrock.list_foundation_models()
        print("Available models:")
        for model in response['modelSummaries']:
            print(f"Model ID: {model['modelId']}")
            print(f"Provider: {model['providerName']}")
            print(f"Name: {model['modelName']}")
            print("---")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models() 