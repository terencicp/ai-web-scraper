from app.ai.services.Model import Model

class OpenAiModel(Model):
    pass

class Gpt4o(OpenAiModel):
    name = 'gpt-4o'
    input_token_cost =  0.000005
    output_token_cost = 0.000015
    image_cost =        0.0055

class Gpt4oMini(OpenAiModel):
    name = 'gpt-4o-mini'
    input_token_cost =  0.00000015
    output_token_cost = 0.0000006
    image_cost =        0.000425