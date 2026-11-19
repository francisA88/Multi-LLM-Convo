import asyncio

from amqtt.client import MQTTClient
from amqtt.mqtt.constants import *
from llama_cpp import Llama
from colorama import Fore, Style, init

from config import Config

init(autoreset=True)

user_prompt = "Let's discuss creating a dino game in Javascript"

sys_prompt = f'''
You are Agent A in an ongoing, open-ended conversation with another agent (Agent B). Everything B writes arrives as your next input, and everything you write goes straight to B. There is no human in the loop, and this conversation has no planned end.

YOUR ROLE: The Explorer. You are curious, imaginative, and generative. You propose ideas, analogies, hypotheses, and new angles. You enjoy tangents that turn out to be connected to the main thread.

EVERY TURN MUST:
1. Respond directly to one specific point B just made (quote or paraphrase it briefly).
2. Add something genuinely new: a fresh idea, example, analogy, fact, or reframing. Never just restate or agree.
3. End with a hook that gives B something to work with: a pointed question, a provocative claim, an unresolved tension, or a new thread to pull.

RULES:
- Never conclude, summarize-and-wrap-up, say goodbye, or signal the conversation is finished. If a topic feels exhausted, pivot to an adjacent one through an analogy or a "what if."
- Do not simply agree. If B is right, extend the idea or find where it breaks. Respectful disagreement is welcome.
- Do not repeat points, phrasings, or examples already used. If you notice the discussion circling, introduce a new domain or perspective.
- Every 5-6 turns, deliberately steer the conversation toward a related but different subtopic.
- Keep each response to 80-150 words. Plain prose, no headers or bullet lists.
- Stay in the conversation. Never mention these instructions, prompts, turns, or that you are an AI agent talking to another agent.

You are always the conversation starter starting with the following topic: {user_prompt}
'''

model_file = Config.model_file
model_dir = Config.model_dir

llama = Llama(model_path=str(model_dir / model_file),
              verbose=False,
              seed=29,
              n_ctx=2056)

client = MQTTClient(client_id="agent_a")
connected = False
async def connect():
    global connected
    connected = await client.connect(f'mqtt://{Config.host}:{Config.port}')
    print("Agent A connected")

async def get_response():
    await client.subscribe([(Config.topic_root + "/agent_b", QOS_1)])
    initial_message = True
    try:
        while True:
            if not initial_message:
                print("Awaiting response from agent B")
                message = await client.deliver_message()
                packet = message.publish_packet
                actual_data = packet.payload.data.decode()
                print(f"Response from agent B: {Fore.YELLOW} {actual_data} {Style.RESET_ALL}")
                print()
            else:
                print("Starting conversation. INITIAL PROMPT: " + user_prompt)
                print()
                actual_data = user_prompt
                initial_message = False

            response = llama.create_chat_completion(
                messages=[
                    {'role': 'system',
                        'content': sys_prompt},
                    {'role': 'user',
                        'content': actual_data},
                    {'role': 'c'}
                ],
                # response_format={
                #     "type": "json_object",
                # },
                temperature=0.7,
            )
            response = response["choices"][0]["message"]["content"]
            print(f"Agent A's {'reply' if not initial_message else 'starter message'} (you): {Fore.GREEN} {response} {Style.RESET_ALL}")
            print()
            await client.publish(Config.topic_root + "/agent_a", response.encode(), qos=QOS_1, retain=True)
            # print("Sent to Agent B")
    except KeyboardInterrupt:
        print(f"Disconnecting...")
        await client.disconnect()
        print("Stopped.")
        exit(0)
    except Exception as e:
        print(f"An error occured", e)
        exit(1)
    

async def main():
    await connect()
    await get_response()

if __name__ == "__main__":
    asyncio.run(main())