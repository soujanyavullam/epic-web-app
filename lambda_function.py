import json
import numpy as np

def lambda_handler(event, context):
    try:
        # Create a simple numpy array
        arr = np.array([1, 2, 3, 4, 5])
        
        # Perform some basic numpy operations
        mean = np.mean(arr)
        sum_val = np.sum(arr)
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Numpy operations successful',
                'array': arr.tolist(),
                'mean': float(mean),
                'sum': int(sum_val)
            })
        }
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error occurred',
                'error': str(e)
            })
        }
    
    return response 