import google.generativeai as genai

genai.configure(api_key="AIzaSyA9TS43rDrJ6H76n7WNbOFkzF5VCJZtB_U")

for model in genai.list_models():
    print(model.name)