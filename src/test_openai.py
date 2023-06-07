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