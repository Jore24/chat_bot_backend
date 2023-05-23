import openai

openai.api_key = "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"

response = openai.Completion.create(
    model="text-davinci-003",
    prompt="Dame un saludo en java para todos mis amigos de universidad",
    temperature=0.9,
    max_tokens=150,
    top_p=1,
    frequency_penalty=0.0,
    presence_penalty=0.6,
    stop=[" Human:", " AI:"]
)

print(response.choices[0].text.strip())