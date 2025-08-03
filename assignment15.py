from openai import OpenAI

API_key = "aa-VIYcdCWFZTHh6G1KSVnyDRmOEjiJWfhDGb6HtCOSTEdQDGVP"
url = "https://api.avalai.ir/v1"

client = OpenAI(api_key=API_key, base_url=url)

tone = input("Enter the tone for the conversation (e.g., sarcastically, cheerfully, angrily):").strip()

if not tone:
    print("Error: Tone cannot be empty.Exiting.")
    exit()

prompts = [
    {
        "role":"system",
        "content":[
            {"type":"text", "text":f"Respond {tone}"}
        ]
    }
]

exit_words = {"quit", "exit", "stop"}

while True:
    message = input("Enter your message (or 'quit', 'exit', 'stop' to end):")

    if not message:
        print("Error: Message cannot be empty. Try again")
        continue

    prompts.append(
        {
            "role":"user", 
            "content": [
                {"type":"text", "text": message}
            ]
        }
    )
    try:
        response = client.chat.completions.create(
            model = "GPT-4.1-nano",
            messages = prompts
        )
        response = response.choices[0].message.count[0].text.strip()
        print(f"AI response ({tone}): {response}")

        prompts.append(
            {
                "role": "assistant",
                "content": [{"type": "text", "text": {response}}]
            }
        )
        print("Conversation History:")
        for m in prompts:
            role = m["role"].capitalize()
            content = [c["text"] for c in m["content"] if c["type"] == "text"]
            for text in content:
                print(f"{role}: {text}")

    except Exception as e:
        print(f"An error occurres: {e}")