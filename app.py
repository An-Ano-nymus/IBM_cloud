from flask import Flask, request, render_template
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning import APIClient
import requests
import json

app = Flask(__name__)

# IBM Watsonx credentials
wml_credentials = {
    "url": "https://us-south.ml.cloud.ibm.com",
    "apikey": "JZ4P9-fJmcGv10Ge6OEFyJUNL_ZsUkmZrCv2IfLAoWU6"
}
project_id = "efa124a5-42ad-4202-b6d9-b184649096e6"

# Initialize Watsonx client
client = APIClient(wml_credentials)
client.set.default_project(project_id)

# Load model
granite_model = Model(
    model_id="ibm/granite-3-8b-instruct",
    credentials=wml_credentials,
    project_id=project_id
)

def build_prompt(idea):
    return f"""
You are a Startup Assistant Agent.

Given the idea: "{idea}", generate a structured startup business blueprint including:

1. Business Model Canvas
2. Estimated Budget
3. Market Research
4. Competitor Analysis
5. Go-to-Market Strategy
6. Potential Funding Options
7. Relevant Indian Government Schemes
8. Legal and Regulatory Requirements

Output each section clearly.
"""


# def generate_blueprint(startup_idea):
#     prompt = build_prompt(startup_idea)
#     parameters = {
#         "max_new_tokens": 8192,
#         "decoding_method": "greedy"
#     }
#     response = granite_model.generate(prompt=prompt, params=parameters)
#     return response




def generate_blueprint(startup_idea):
    API_KEY = "JZ4P9-fJmcGv10Ge6OEFyJUNL_ZsUkmZrCv2IfLAoWU6"  # ✅ Your API key
    try:
        # Step 1: Get bearer token
        token_response = requests.post(
            'https://iam.cloud.ibm.com/identity/token',
            data={"apikey": API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'}
        )
        if token_response.status_code != 200:
            return {"results": [{"generated_text": "Failed to retrieve token"}]}
        
        mltoken = token_response.json()["access_token"]

        # Step 2: Build prompt
        prompt = build_prompt(startup_idea)

        # Step 3: Construct headers and payload
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {mltoken}'
        }
        payload_scoring = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        # Step 4: POST to deployment endpoint
        response = requests.post(
            'https://us-south.ml.cloud.ibm.com/ml/v4/deployments/40d3310c-78b7-49b8-a5e3-6f6bf0c5d1ef/ai_service_stream?version=2021-05-01',
            json=payload_scoring,
            headers=headers,
            stream=True  # <== stream is needed for streaming responses
        )
        parsed_output = parse_watson_response(response)
        return {"results": [{"generated_text": parsed_output}]}
        if response.status_code != 200:
            return {"results": [{"generated_text": f"Watsonx API error: {response.status_code} - {response.text}"}]}

        # Step 5: Parse response JSON safely
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"results": [{"generated_text": "Invalid JSON in Watson response."}]}

    except Exception as e:
        return {"results": [{"generated_text": f"Exception occurred: {e}"}]}



import json

def parse_watson_response(response):
    try:
        result_text = ""

        # Iterate through response lines (streamed format)
        for line in response.iter_lines():
            if line:
                # Decode byte line to string
                line_str = line.decode('utf-8')

                # Only process lines that start with "data:"
                if line_str.startswith("data:"):
                    try:
                        json_data = json.loads(line_str[len("data:"):].strip())
                        content = json_data.get("message", {}).get("content", "")
                        result_text += content
                    except json.JSONDecodeError:
                        continue  # skip invalid JSON fragments

        return result_text.strip() if result_text else "No valid content found."

    except Exception as e:
        return f"Error parsing response: {e}"





# @app.route("/", methods=["GET", "POST"])
# def index():
#     result = ""
#     if request.method == "POST":
#         idea = request.form["idea"]

#         response = generate_blueprint(idea)
#         result = response
#         result = response.get("results", "No response generated.")
#         result= result[0].get("generated_text", "No Response")

#     return render_template("index.html", result=result)


@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        idea = request.form["idea"]
        response = generate_blueprint(idea)

        # Parse Watson output format
        result = response.get("results", [{"generated_text": "No result"}])[0].get("generated_text", "No generated text")

    return render_template("index.html", result=result)





if __name__ == "__main__":
    app.run(debug=True)
