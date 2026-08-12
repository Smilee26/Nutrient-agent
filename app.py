import os
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai import Credentials

def get_ibm_granite_response(prompt: str, system_prompt: str = "") -> str:
    api_key = os.getenv("IBM_CLOUD_API_KEY", "YOUR_IBM_API_KEY")
    project_id = os.getenv("IBM_PROJECT_ID", "YOUR_WATSONX_PROJECT_ID")
    
    credentials = Credentials(
        url="https://us-south.ml.cloud.ibm.com",
        api_key=api_key
    )
    
    # Using IBM Granite 3.0 model
    model = ModelInference(
        model_id="ibm/granite-3-8b-instruct",
        credentials=credentials,
        project_id=project_id,
        params={
            "max_new_tokens": 800,
            "temperature": 0.3
        }
    )
    
    full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{prompt}\n<|assistant|>"
    response = model.generate_text(prompt=full_prompt)
    return response