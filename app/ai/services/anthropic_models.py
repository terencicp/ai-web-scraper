from app.ai.services.Model import Model

class AnthropicModel(Model):
    pass

class Claude35Sonnet(AnthropicModel):
    name = 'claude-3-5-sonnet-20240620'
    input_token_cost = 0.000003
    output_token_cost = 0.000015
    image_cost = 0.000425