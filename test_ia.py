from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1-mini",
    input="Explicame qué es una red neuronal en términos simples."
)

print(response.output[0].content[0].text)
